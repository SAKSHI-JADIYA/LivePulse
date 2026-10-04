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


# ============================================================
# SESSION STATE
# ============================================================

if "running" not in st.session_state:
    st.session_state.running = False


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
signal_placeholder = st.empty()
timeline_placeholder = st.empty()


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

    behavior_history = deque(maxlen=20)

    status_placeholder.info(
        f"Monitoring {target}..."
    )

    packet_stream = capture.start()

    try:

        for line in packet_stream:

            if not st.session_state.running:
                break

            packet = parse_packet(line)

            if packet is None:
                continue


            # ====================================================
            # TIMEOUT / PACKET LOSS
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

                behavior_history.append({
                    "event": "Packet Loss",
                    "behavior": result["behavior"],
                    "status": result["status"],
                    "match": result["match"]
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

                signals = metrics.analyze_behavior(
                    rtt=rtt
                )

                result = metrics.detect_behavior(
                    signals
                )

                metrics.record_observation(rtt)

                rtt_values.append(rtt)
                rtt_times.append(
                    pd.Timestamp.now()
                )

                behavior_history.append({
                    "event": "Reply",
                    "behavior": result["behavior"],
                    "status": result["status"],
                    "match": result["match"]
                })


            # ====================================================
            # DASHBOARD DATA
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

            if behavior_history:

                latest = behavior_history[-1]

                behavior_metric.metric(
                    "Current Behavior",
                    latest["behavior"]
                )

            else:

                behavior_metric.metric(
                    "Current Behavior",
                    "Normal"
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

            signal_placeholder.subheader(
                "Latest behavior signals"
            )

            signal_cols = signal_placeholder.columns(5)

            signal_cols[0].metric(
                "RTT Spike",
                signals.get("rtt_spike", 0)
                if "signals" in locals()
                else 0
            )

            signal_cols[1].metric(
                "Instability",
                signals.get("rtt_instability", 0)
                if "signals" in locals()
                else 0
            )

            signal_cols[2].metric(
                "Sudden Change",
                signals.get("sudden_rtt_change", 0)
                if "signals" in locals()
                else 0
            )

            signal_cols[3].metric(
                "Traffic Burst",
                signals.get("traffic_burst", 0)
                if "signals" in locals()
                else 0
            )

            signal_cols[4].metric(
                "Packet Loss",
                signals.get("packet_loss", 0)
                if "signals" in locals()
                else 0
            )


            # ====================================================
            # RECENT BEHAVIOR
            # ====================================================

            if behavior_history:

                timeline = pd.DataFrame(
                    list(behavior_history)
                )

                timeline_placeholder.subheader(
                    "Recent behavior"
                )

                timeline_placeholder.dataframe(
                    timeline.iloc[::-1],
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

        - Real-time RTT
        - Jitter
        - Packet loss
        - Behavioral signals
        - Current behavior classification
        - Recent behavior timeline

        **Architecture:** TShark → Parser → Metrics → Behavior Signals → Behavior Matrix → Dashboard
        """
    )
