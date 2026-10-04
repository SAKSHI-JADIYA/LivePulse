import subprocess


class TSharkCapture:

    def __init__(self, interface, target):

        self.interface = interface
        self.target = target
        self.process = None

    def start(self):

        command = [
            "tshark",

            "-i",
            self.interface,

            "-f",
            f"icmp and host {self.target}",

            "-T",
            "fields",

            "-e",
            "frame.time_epoch",

            "-e",
            "ip.src",

            "-e",
            "ip.dst",

            "-e",
            "icmp.type",

            "-e",
            "icmp.seq",

            "-l"
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        return self.process.stdout

    def stop(self):

        if self.process and self.process.poll() is None:

            self.process.terminate()