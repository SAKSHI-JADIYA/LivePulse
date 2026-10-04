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

    "Sudden RTT Change": {
        "rtt_spike": 0,
        "rtt_instability": 0,
        "sudden_rtt_change": 1,
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


FEATURE_NAMES = [
    "rtt_spike",
    "rtt_instability",
    "sudden_rtt_change",
    "traffic_burst"
]


# ============================================================
# NETWORK METRICS
# ============================================================

class NetworkMetrics:

    def __init__(self, history_size=20):

        # Request sequence -> request timestamp
        self.pending_requests = {}

        # Previous RTT values
        self.rtt_history = deque(
            maxlen=history_size
        )

        # Request timestamps
        self.request_times = deque(
            maxlen=history_size
        )

        # Previous request intervals
        self.request_intervals = deque(
            maxlen=history_size
        )

        self.latest_request_interval = None

        self.received = 0
        self.lost = 0

        self.previous_rtt = None


    # ========================================================
    # REQUEST PROCESSING
    # ========================================================

    def process_request(self, packet):

        # Calculate interval using PREVIOUS request.
        # The current interval is not yet added to history.
        if self.request_times:

            self.latest_request_interval = (
                packet.timestamp
                - self.request_times[-1]
            )

        else:

            self.latest_request_interval = None

        self.pending_requests[
            packet.sequence
        ] = packet.timestamp

        self.request_times.append(
            packet.timestamp
        )


    # ========================================================
    # REPLY PROCESSING
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

        self.received += 1

        return rtt_ms


    # ========================================================
    # RECORD CURRENT OBSERVATION
    # ========================================================

    def record_observation(self, rtt):

        # Current RTT is added AFTER analysis.
        self.rtt_history.append(
            rtt
        )

        if self.latest_request_interval is not None:

            self.request_intervals.append(
                self.latest_request_interval
            )

        self.previous_rtt = rtt


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
    # BEHAVIOR ANALYSIS
    # ========================================================

    def analyze_behavior(self, rtt):

        signals = {
            "rtt_spike": 0,
            "rtt_instability": 0,
            "sudden_rtt_change": 0,
            "traffic_burst": 0
        }

        # ----------------------------------------------------
        # We need enough PREVIOUS observations first.
        # ----------------------------------------------------

        if len(self.rtt_history) >= 5:

            average_rtt = mean(
                self.rtt_history
            )

            deviation = stdev(
                self.rtt_history
            )

            # -----------------------------------------------
            # 1. RTT SPIKE
            # -----------------------------------------------

            if deviation > 0:

                if rtt > average_rtt + (2 * deviation):

                    signals["rtt_spike"] = 1

            # -----------------------------------------------
            # 2. RTT INSTABILITY
            # -----------------------------------------------

            if average_rtt > 0:

                variation = (
                    deviation / average_rtt
                )

                if variation > 0.25:

                    signals[
                        "rtt_instability"
                    ] = 1

            # -----------------------------------------------
            # 3. SUDDEN RTT CHANGE
            # -----------------------------------------------

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
        # 4. TRAFFIC BURST
        # ----------------------------------------------------

        if (
            self.latest_request_interval is not None
            and len(self.request_intervals) >= 2
        ):

            average_interval = mean(
                self.request_intervals
            )

            if (
                average_interval > 0
                and self.latest_request_interval
                < average_interval * 0.5
            ):

                signals[
                    "traffic_burst"
                ] = 1

        return signals


    # ========================================================
    # MATRIX DECISION
    # ========================================================

    def detect_behavior(self, signals):

        # ----------------------------------------------------
        # No signals = Normal
        # ----------------------------------------------------

        if all(
            signals[name] == 0
            for name in FEATURE_NAMES
        ):

            return {
                "behavior": "Normal",
                "status": "Normal",
                "match": 100,
                "matched": [],
                "missing": [],
                "unexpected": []
            }


        observed = {
            name
            for name in FEATURE_NAMES
            if signals[name] == 1
        }


        best_behavior = None
        best_score = -1
        best_matched = []
        best_missing = []
        best_unexpected = []


        # ----------------------------------------------------
        # Compare observed behavior against every pattern
        # ----------------------------------------------------

        for behavior, pattern in BEHAVIOR_MATRIX.items():

            if behavior == "Normal":
                continue

            expected = {
                name
                for name in FEATURE_NAMES
                if pattern[name] == 1
            }

            matched = observed & expected

            missing = expected - observed

            unexpected = observed - expected

            # Similarity is based on active signals.
            denominator = max(
                len(observed),
                len(expected)
            )

            if denominator == 0:
                continue

            score = (
                len(matched)
                / denominator
            )

            if score > best_score:

                best_score = score
                best_behavior = behavior

                best_matched = sorted(
                    matched
                )

                best_missing = sorted(
                    missing
                )

                best_unexpected = sorted(
                    unexpected
                )


        match_percentage = round(
            best_score * 100
        )


        # ----------------------------------------------------
        # Exact match
        # ----------------------------------------------------

        if (
            set(best_matched) == observed
            and not best_missing
            and not best_unexpected
        ):

            status = "Detected"

        # ----------------------------------------------------
        # Partial match
        # ----------------------------------------------------

        elif match_percentage >= 50:

            status = "Possible"

        # ----------------------------------------------------
        # Weak match
        # ----------------------------------------------------

        else:

            status = "Unclassified"


        return {
            "behavior": best_behavior,
            "status": status,
            "match": match_percentage,
            "matched": best_matched,
            "missing": best_missing,
            "unexpected": best_unexpected
        }


    # ========================================================
    # STATISTICS
    # ========================================================

    def get_stats(self):

        return {
            "received": self.received,
            "lost": self.lost,
            "average_rtt": self.get_average_rtt(),
            "min_rtt": self.get_min_rtt(),
            "max_rtt": self.get_max_rtt(),
            "jitter": self.get_jitter()
        }