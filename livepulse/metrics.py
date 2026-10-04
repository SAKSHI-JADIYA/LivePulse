from collections import deque
from statistics import mean, stdev


# ============================================================
# BEHAVIOR MATRIX
# ============================================================

BEHAVIOR_MATRIX = {

    "Normal": {
        "rtt_spike": 0,
        "rtt_instability": 0,
        "sudden_rtt_change": 0,
        "traffic_burst": 0
    },

    "Latency Spike": {
        "rtt_spike": 1,
        "rtt_instability": 0,
        "sudden_rtt_change": 0,
        "traffic_burst": 0
    },

    "Network Instability": {
        "rtt_spike": 1,
        "rtt_instability": 1,
        "sudden_rtt_change": 1,
        "traffic_burst": 0
    },

    "Traffic Burst": {
        "rtt_spike": 0,
        "rtt_instability": 0,
        "sudden_rtt_change": 0,
        "traffic_burst": 1
    },

    "Network Stress": {
        "rtt_spike": 1,
        "rtt_instability": 1,
        "sudden_rtt_change": 1,
        "traffic_burst": 1
    }
}


# ============================================================
# NETWORK METRICS + BEHAVIOR ANALYSIS
# ============================================================

class NetworkMetrics:

    def __init__(self, history_size=20):

        # -------------------------
        # Request/reply tracking
        # -------------------------

        self.pending_requests = {}

        # -------------------------
        # RTT history
        # -------------------------

        self.rtt_history = deque(
            maxlen=history_size
        )

        # -------------------------
        # Request timing history
        # -------------------------

        self.request_times = deque(
            maxlen=history_size
        )

        # -------------------------
        # Counters
        # -------------------------

        self.received = 0
        self.lost = 0

        # -------------------------
        # Previous RTT
        # -------------------------

        self.previous_rtt = None


    # ========================================================
    # REQUEST
    # ========================================================

    def process_request(self, packet):

        self.pending_requests[
            packet.sequence
        ] = packet.timestamp

        self.request_times.append(
            packet.timestamp
        )


    # ========================================================
    # REPLY
    # ========================================================

    def process_reply(self, packet):

        sequence = packet.sequence

        if sequence not in self.pending_requests:

            return None

        request_time = self.pending_requests.pop(
            sequence
        )

        rtt_ms = (
            packet.timestamp - request_time
        ) * 1000

        self.rtt_history.append(
            rtt_ms
        )

        self.received += 1

        return rtt_ms


    # ========================================================
    # BASIC METRICS
    # ========================================================

    def get_average_rtt(self):

        if not self.rtt_history:
            return None

        return mean(
            self.rtt_history
        )


    def get_min_rtt(self):

        if not self.rtt_history:
            return None

        return min(
            self.rtt_history
        )


    def get_max_rtt(self):

        if not self.rtt_history:
            return None

        return max(
            self.rtt_history
        )


    def get_jitter(self):

        if len(self.rtt_history) < 2:
            return None

        values = list(
            self.rtt_history
        )

        differences = []

        for i in range(1, len(values)):

            differences.append(
                abs(
                    values[i] - values[i - 1]
                )
            )

        return mean(
            differences
        )


    # ========================================================
    # BEHAVIORAL SIGNALS
    # ========================================================

    def analyze_behavior(self, rtt):

        signals = {

            "rtt_spike": 0,

            "rtt_instability": 0,

            "sudden_rtt_change": 0,

            "traffic_burst": 0
        }


        # ----------------------------------------------------
        # We need some history before analyzing behavior
        # ----------------------------------------------------

        if len(self.rtt_history) >= 5:

            average_rtt = mean(
                self.rtt_history
            )

            deviation = stdev(
                self.rtt_history
            )


            # ------------------------------------------------
            # RTT SPIKE
            # ------------------------------------------------

            if deviation > 0:

                if rtt > average_rtt + (2 * deviation):

                    signals["rtt_spike"] = 1


            # ------------------------------------------------
            # RTT INSTABILITY
            # ------------------------------------------------

            if average_rtt > 0:

                variation = (
                    deviation / average_rtt
                )

                if variation > 0.25:

                    signals["rtt_instability"] = 1


            # ------------------------------------------------
            # SUDDEN RTT CHANGE
            # ------------------------------------------------

            if self.previous_rtt is not None:

                change = abs(
                    rtt - self.previous_rtt
                )

                if (
                    deviation > 0
                    and change > 2 * deviation
                ):

                    signals[
                        "sudden_rtt_change"
                    ] = 1


        # ----------------------------------------------------
        # TRAFFIC BURST
        # ----------------------------------------------------

        if len(self.request_times) >= 3:

            times = list(
                self.request_times
            )

            intervals = []

            for i in range(1, len(times)):

                interval = (
                    times[i] - times[i - 1]
                )

                intervals.append(
                    interval
                )

            average_interval = mean(
                intervals
            )

            if (
                average_interval > 0
                and intervals[-1]
                < average_interval * 0.5
            ):

                signals[
                    "traffic_burst"
                ] = 1


        self.previous_rtt = rtt

        return signals


    # ========================================================
    # MATRIX DECISION
    # ========================================================

    def detect_behavior(self, signals):

        feature_names = [

            "rtt_spike",

            "rtt_instability",

            "sudden_rtt_change",

            "traffic_burst"
        ]


        # ----------------------------------------------------
        # Everything normal
        # ----------------------------------------------------

        if all(
            signals[name] == 0
            for name in feature_names
        ):

            return {
                "behavior": "Normal",
                "confidence": 100
            }


        best_behavior = None
        best_score = -1


        # ----------------------------------------------------
        # Compare observed pattern with matrix
        # ----------------------------------------------------

        for behavior, pattern in BEHAVIOR_MATRIX.items():

            matches = 0

            for name in feature_names:

                if (
                    signals[name]
                    == pattern[name]
                ):

                    matches += 1


            score = (
                matches
                / len(feature_names)
            )


            if score > best_score:

                best_score = score

                best_behavior = behavior


        return {

            "behavior": best_behavior,

            "confidence": round(
                best_score * 100
            )
        }


    # ========================================================
    # ALL STATISTICS
    # ========================================================

    def get_stats(self):

        return {

            "received": self.received,

            "lost": self.lost,

            "average_rtt":
                self.get_average_rtt(),

            "min_rtt":
                self.get_min_rtt(),

            "max_rtt":
                self.get_max_rtt(),

            "jitter":
                self.get_jitter()
        }