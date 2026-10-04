from .capture import TSharkCapture
from .parser import parse_packet
from .metrics import NetworkMetrics


class LivePulseMonitor:

    def __init__(
        self,
        interface,
        target
    ):

        self.target = target

        self.capture = TSharkCapture(
            interface=interface,
            target=target
        )

        self.metrics = NetworkMetrics(
            timeout_seconds=2.0
        )


    def start(self):

        print()
        print("=" * 60)
        print("                    LIVEPULSE")
        print("          REAL-TIME NETWORK MONITOR")
        print("=" * 60)

        print()

        print(
            f"Target: {self.target}"
        )

        print()

        print(
            "Starting live packet capture..."
        )

        print()

        packet_stream = self.capture.start()

        try:

            for line in packet_stream:

                packet = parse_packet(line)

                if packet is None:
                    continue


                # ====================================================
                # CHECK FOR OLD REQUESTS THAT TIMED OUT
                # ====================================================

                lost_sequences = (
                    self.metrics.check_timeouts(
                        packet.timestamp
                    )
                )


                for sequence in lost_sequences:

                    signals = (
                        self.metrics.analyze_behavior(
                            packet_loss=True
                        )
                    )

                    result = (
                        self.metrics.detect_behavior(
                            signals
                        )
                    )

                    print(
                        f"✕ TIMEOUT "
                        f"seq={sequence}"
                    )

                    print(
                        "   Packet Loss Detected"
                    )

                    print(
                        f"   Behavior: "
                        f"{result['status']} "
                        f"{result['behavior']} "
                        f"(Match: "
                        f"{result['match']}%)"
                    )

                    print()


                # ====================================================
                # ICMP REQUEST
                # ====================================================

                if (
                    packet.icmp_type == 8
                    and packet.destination == self.target
                ):

                    self.metrics.process_request(
                        packet
                    )

                    print(
                        f"→ REQUEST "
                        f"seq={packet.sequence}"
                    )


                # ====================================================
                # ICMP REPLY
                # ====================================================

                elif (
                    packet.icmp_type == 0
                    and packet.source == self.target
                ):

                    rtt = (
                        self.metrics.process_reply(
                            packet
                        )
                    )

                    if rtt is None:
                        continue


                    # Analyze BEFORE storing current RTT

                    signals = (
                        self.metrics.analyze_behavior(
                            rtt=rtt
                        )
                    )


                    result = (
                        self.metrics.detect_behavior(
                            signals
                        )
                    )


                    stats = (
                        self.metrics.get_stats()
                    )


                    # Store current RTT AFTER analysis

                    self.metrics.record_observation(
                        rtt
                    )


                    # =================================================
                    # OUTPUT
                    # =================================================

                    print(
                        f"← REPLY "
                        f"seq={packet.sequence} "
                        f"RTT={rtt:.2f} ms"
                    )


                    if stats["average_rtt"] is not None:

                        print(
                            f"   Average: "
                            f"{stats['average_rtt']:.2f} ms"
                        )


                    if stats["jitter"] is not None:

                        print(
                            f"   Jitter: "
                            f"{stats['jitter']:.2f} ms"
                        )


                    print(
                        f"   Packet Loss: "
                        f"{stats['packet_loss']:.2f}%"
                    )


                    print(
                        f"   Signals: "
                        f"RTT-Spike="
                        f"{signals['rtt_spike']} "
                        f"Instability="
                        f"{signals['rtt_instability']} "
                        f"Sudden-Change="
                        f"{signals['sudden_rtt_change']} "
                        f"Burst="
                        f"{signals['traffic_burst']} "
                        f"Loss="
                        f"{signals['packet_loss']}"
                    )


                    if result["status"] == "Normal":

                        print(
                            "   Behavior: Normal"
                        )

                    else:

                        print(
                            f"   Behavior: "
                            f"{result['status']} "
                            f"{result['behavior']} "
                            f"(Match: "
                            f"{result['match']}%)"
                        )

                        if result["matched"]:

                            print(
                                "   Matched: "
                                + ", ".join(
                                    result["matched"]
                                )
                            )

                        if result["missing"]:

                            print(
                                "   Missing: "
                                + ", ".join(
                                    result["missing"]
                                )
                            )

                        if result["unexpected"]:

                            print(
                                "   Unexpected: "
                                + ", ".join(
                                    result["unexpected"]
                                )
                            )


                    print()


        except KeyboardInterrupt:

            print()
            print(
                "Stopping LivePulse..."
            )


        finally:

            self.capture.stop()

            self.show_summary()


    def show_summary(self):

        stats = self.metrics.get_stats()

        print()
        print("=" * 60)
        print("                       SUMMARY")
        print("=" * 60)

        print(
            f"Total packets: "
            f"{stats['total']}"
        )

        print(
            f"Packets received: "
            f"{stats['received']}"
        )

        print(
            f"Packets lost: "
            f"{stats['lost']}"
        )

        print(
            f"Packet loss: "
            f"{stats['packet_loss']:.2f}%"
        )


        if stats["average_rtt"] is not None:

            print(
                f"Average RTT: "
                f"{stats['average_rtt']:.2f} ms"
            )


        if stats["min_rtt"] is not None:

            print(
                f"Minimum RTT: "
                f"{stats['min_rtt']:.2f} ms"
            )


        if stats["max_rtt"] is not None:

            print(
                f"Maximum RTT: "
                f"{stats['max_rtt']:.2f} ms"
            )


        if stats["jitter"] is not None:

            print(
                f"Jitter: "
                f"{stats['jitter']:.2f} ms"
            )

        print()