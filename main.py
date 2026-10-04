import subprocess
import statistics

# Your Wi-Fi interface number
INTERFACE = "4"

# IP address we are monitoring
TARGET = "8.8.8.8"

# TShark command
tshark_command = [
    "tshark",
    "-i", INTERFACE,
    "-f", f"icmp and host {TARGET}",
    "-T", "fields",
    "-e", "frame.time_epoch",
    "-e", "ip.src",
    "-e", "ip.dst",
    "-e", "icmp.type",
    "-e", "icmp.seq",
    "-l"
]

# Start TShark
tshark = subprocess.Popen(
    tshark_command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

print("NetPulse started...")
print(f"Monitoring: {TARGET}")
print("Waiting for ICMP packets...\n")

# Store request timestamps
requests = {}

# STEP 14:
# Store all calculated RTT values
rtt_values = []

# Read packets continuously
for line in tshark.stdout:

    # Remove whitespace and newline
    line = line.strip()

    # Ignore empty lines
    if not line:
        continue

    # Split TShark output into fields
    fields = line.split("\t")

    # We expect 5 fields
    if len(fields) != 5:
        continue

    timestamp, source, destination, icmp_type, sequence = fields

    # Convert values into useful Python types
    timestamp = float(timestamp)
    icmp_type = int(icmp_type)
    sequence = int(sequence)

    # ICMP Echo Request
    if icmp_type == 8:

        requests[sequence] = timestamp

        print(
            f"REQUEST  seq={sequence} "
            f"time={timestamp}"
        )

    # ICMP Echo Reply
    elif icmp_type == 0:

        # Check whether we saw the matching request
        if sequence in requests:

            request_time = requests[sequence]

            # Calculate RTT in milliseconds
            rtt = (timestamp - request_time) * 1000

            # STEP 14:
            # Save RTT
            rtt_values.append(rtt)

            print(
                f"REPLY    seq={sequence} "
                f"RTT={rtt:.2f} ms"
            )

            # STEP 15:
            # Calculate baseline statistics
            if len(rtt_values) >= 5:

                average_rtt = statistics.mean(rtt_values)
                minimum_rtt = min(rtt_values)
                maximum_rtt = max(rtt_values)
                rtt_std = statistics.stdev(rtt_values)

                print(
                    f"BASELINE | "
                    f"AVG={average_rtt:.2f} ms | "
                    f"MIN={minimum_rtt:.2f} ms | "
                    f"MAX={maximum_rtt:.2f} ms | "
                    f"STD={rtt_std:.2f} ms"
                )

            # Request has now been matched
            del requests[sequence]