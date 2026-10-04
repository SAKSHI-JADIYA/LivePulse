import time
from collections import deque

import pandas as pd
import streamlit as st

from livepulse.capture import TSharkCapture
from livepulse.parser import parse_packet
from livepulse.metrics import NetworkMetrics


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="LivePulse",
    page_icon="📡",
    layout="wide"
)


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_INTERFACE = "1"
DEFAULT_TARGET = "8.8.8.8"
TIMEOUT_SECONDS = 2.0
MAX_POINTS = 60
MAX_EVENTS = 30


# ============================================================
# HEADER
# ============================================================

st.title("📡 LIVEPULSE")
st.caption("Real-time network behavior monitor")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Configuration")

    interface = st.text_input(
        "TShark interface",
        value=DEFAULT_INTERFACE
    )

    target = st.text_input(
        "Target",
        value=DEFAULT_TARGET
    )

    st.write(
        f"Timeout: {TIMEOUT_SECONDS:.1f} seconds"
    )

    start = st.button(
        "▶ Start monitoring",
        use_container_width=True
    )

    stop = st.button(
        "■ Stop monitoring",
        use_container_width=True
    )


# ============================================================
# SESSION STATE
# ============================================================

if "running" not in st.session_state:
    st.session_state.running = False

if start:
    st.session_state.running = True

if stop:
    st.session_state.running = False


# ============================================================
# PLACEHOLDERS
# ============================================================

status_placeholder = st.empty()

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

avg_metric = metric_col1.empty()
jitter_metric = metric_col2.empty()
loss_metric = metric_col3.empty()
behavior_metric = metric_col4.empty()

chart_placeholder = st.empty()

st.divider()

st.subheader("Latest signals")

signal_cols = st.columns(5)

signal_rtt = signal_cols[0].empty()
signal_instability = signal_cols[1].empty()
signal_sudden = signal_cols[2].empty()
signal_burst = signal_cols[3].empty()
signal_loss = signal_cols[4].empty()

st.divider()

st.subheader("Live event log")

event_placeholder = st.empty()


# ============================================================
# LIVE MONITOR
# ============================================================

if st.session_state.running:

    capture = TSharkCapture(
        interface=interface,
        target=target
    )

    metrics = NetworkMetrics(
        timeout_seconds=TIMEOUT_SECONDS
    )

    rtt_values = deque(maxlen=MAX_POINTS)
    rtt_times = deque(maxlen=MAX_POINTS)

    events = deque(maxlen=MAX_EVENTS)

    status_placeholder.info(
        f"Monitoring {target}..."
    )

    packet_stream = capture.start()

    latest_signals = {
        "rtt_spike": 0,
        "rtt_instability": 0,
        "sudden_rtt_change": 0,
        "traffic_burst": 0,
        "packet_loss": 0
    }

    latest_behavior = "Normal"


    try:

        for line in packet_stream:

            if not st.session_state.running:
                break

            packet = parse_packet(line)

            if packet is None:
                continue


            # ====================================================
            # CHECK TIMEOUTS
            # ====================================================

            lost_sequences = metrics.check_timeouts(
                packet.timestamp
            )

            for sequence in lost_sequences:

                signals = metrics.analyze_behavior(
                    packet_loss=True
                )

                result = metrics.detect_behavior(
                    signals
                )

                stats = metrics.get_stats()

                latest_signals = signals
                latest_behavior = result["behavior"]

                events.append({
                    "Time": pd.Timestamp.now().strftime(
                        "%H:%M:%S"
                    ),
                    "Event": "TIMEOUT",
                    "Seq": sequence,
                    "RTT (ms)": "—",
                    "Average (ms)": (
                        f"{stats['average_rtt']:.2f}"
                        if stats["average_rtt"] is not None
                        else "—"
                    ),
                    "Jitter (ms)": (
                        f"{stats['jitter']:.2f}"
                        if stats["jitter"] is not None
                        else "—"
                    ),
                    "Loss %": f"{stats['packet_loss']:.2f}",
                    "Signals": (
                        f"Spike={signals['rtt_spike']} | "
                        f"Instability={signals['rtt_instability']} | "
                        f"Sudden={signals['sudden_rtt_change']} | "
                        f"Burst={signals['traffic_burst']} | "
                        f"Loss={signals['packet_loss']}"
                    ),
                    "Behavior": result["behavior"],
                    "Status": result["status"],
                    "Match %": result["match"]
                })


            # ====================================================
            # REQUEST
            # ====================================================

            if (
                packet.icmp_type == 8
                and packet.destination == target
            ):

                metrics.process_request(packet)


            # ====================================================
            # REPLY
            # ====================================================

            elif (
                packet.icmp_type == 0
                and packet.source == target
            ):

                rtt = metrics.process_reply(packet)

                if rtt is None:
                    continue


                # Analyze BEFORE storing current RTT

                signals = metrics.analyze_behavior(
                    rtt=rtt
                )

                result = metrics.detect_behavior(
                    signals
                )

                # Store after analysis

                metrics.record_observation(rtt)

                stats = metrics.get_stats()

                latest_signals = signals
                latest_behavior = result["behavior"]


                # =================================================
                # CHART DATA
                # =================================================

                rtt_values.append(rtt)

                rtt_times.append(
                    pd.Timestamp.now()
                )


                # =================================================
                # DETAILED EVENT
                # =================================================

                events.append({
                    "Time": pd.Timestamp.now().strftime(
                        "%H:%M:%S"
                    ),
                    "Event": "REPLY",
                    "Seq": packet.sequence,
                    "RTT (ms)": f"{rtt:.2f}",
                    "Average (ms)": (
                        f"{stats['average_rtt']:.2f}"
                        if stats["average_rtt"] is not None
                        else "—"
                    ),
                    "Jitter (ms)": (
                        f"{stats['jitter']:.2f}"
                        if stats["jitter"] is not None
                        else "—"
                    ),
                    "Loss %": f"{stats['packet_loss']:.2f}",
                    "Signals": (
                        f"Spike={signals['rtt_spike']} | "
                        f"Instability={signals['rtt_instability']} | "
                        f"Sudden={signals['sudden_rtt_change']} | "
                        f"Burst={signals['traffic_burst']} | "
                        f"Loss={signals['packet_loss']}"
                    ),
                    "Behavior": result["behavior"],
                    "Status": result["status"],
                    "Match %": result["match"]
                })


            # ====================================================
            # DASHBOARD METRICS
            # ====================================================

            stats = metrics.get_stats()

            avg = stats["average_rtt"]
            jitter = stats["jitter"]
            loss = stats["packet_loss"]

            avg_metric.metric(
                "Average RTT",
                f"{avg:.2f} ms" if avg is not None else "—"
            )

            jitter_metric.metric(
                "Jitter",
                f"{jitter:.2f} ms" if jitter is not None else "—"
            )

            loss_metric.metric(
                "Packet Loss",
                f"{loss:.2f}%"
            )

            behavior_metric.metric(
                "Current Behavior",
                latest_behavior
            )


            # ====================================================
            # RTT CHART
            # ====================================================

            if rtt_values:

                chart_data = pd.DataFrame({
                    "Time": list(rtt_times),
                    "RTT (ms)": list(rtt_values)
                })

                chart_data = chart_data.set_index(
                    "Time"
                )

                chart_placeholder.line_chart(
                    chart_data,
                    y="RTT (ms)",
                    use_container_width=True
                )


            # ====================================================
            # SIGNALS
            # ====================================================

            signal_rtt.metric(
                "RTT Spike",
                latest_signals["rtt_spike"]
            )

            signal_instability.metric(
                "Instability",
                latest_signals["rtt_instability"]
            )

            signal_sudden.metric(
                "Sudden Change",
                latest_signals["sudden_rtt_change"]
            )

            signal_burst.metric(
                "Traffic Burst",
                latest_signals["traffic_burst"]
            )

            signal_loss.metric(
                "Packet Loss",
                latest_signals["packet_loss"]
            )


            # ====================================================
            # EVENT LOG
            # ====================================================

            if events:

                event_data = pd.DataFrame(
                    list(events)
                )

                event_placeholder.dataframe(
                    event_data.iloc[::-1],
                    use_container_width=True,
                    hide_index=True
                )



            time.sleep(0.05)


    except KeyboardInterrupt:

        pass

    finally:

        capture.stop()

        status_placeholder.success(
            "Monitoring stopped."
        )

else:

    status_placeholder.info(
        "Configure the target and click Start monitoring."
    )

    st.markdown(
        """
        ### What LivePulse shows

        **Metrics**
        - RTT
        - Jitter
        - Packet loss

        **Behavior**
        - RTT spike
        - RTT instability
        - Sudden RTT change
        - Traffic burst
        - Packet loss

        **Architecture**

        `TShark → Parser → Metrics → Behavioral Signals → Behavior Matrix → Dashboard`
        """
    )
