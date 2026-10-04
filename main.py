from livepulse.monitor import LivePulseMonitor


INTERFACE = "4"

TARGET = "8.8.8.8"


monitor = LivePulseMonitor(
    interface=INTERFACE,
    target=TARGET
)

monitor.start()