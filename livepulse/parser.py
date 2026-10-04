from dataclasses import dataclass


@dataclass
class Packet:

    timestamp: float
    source: str
    destination: str
    icmp_type: int
    sequence: int


def parse_packet(line):

    line = line.strip()

    if not line:
        return None

    parts = line.split("\t")

    if len(parts) != 5:
        return None

    timestamp, source, destination, icmp_type, sequence = parts

    try:

        return Packet(
            timestamp=float(timestamp),
            source=source,
            destination=destination,
            icmp_type=int(icmp_type),
            sequence=int(sequence)
        )

    except ValueError:

        return None