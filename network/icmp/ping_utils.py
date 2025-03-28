import socket
import struct


def to_ip(addr: str) -> str:
    """Converts a domain name to an IP address.

    Args:
        addr (str): Domain name or IP address.

    Returns:
        str: IP address as a string.
    """
    try:
        return socket.gethostbyname(addr)
    except socket.gaierror:
        raise ValueError(f"Unable to resolve {addr}")


def is_valid_ip4_address(addr: str) -> bool:
    """Checks if a string is a valid IPv4 address.

    Args:
        addr (str): String containing the potential IP address.

    Returns:
        bool: True if the address is valid, otherwise False.
    """
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False


def calculate_checksum(data: bytes) -> int:
    """Calculates the checksum for an ICMP packet.

    Args:
        data (bytes): Packet data.

    Returns:
        int: Computed checksum.
    """
    checksum = 0
    for i in range(0, len(data), 2):
        checksum += (data[i] << 8) + (
            struct.unpack('B', data[i + 1:i + 2])[0]
            if len(data[i + 1:i + 2]) else 0
        )

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum = ~checksum & 0xFFFF
    return checksum


def calculate_rtt(responses: list) -> float:
    """Calculates the average round-trip time (RTT).

    Args:
        responses (list): List of response times (in milliseconds).

    Returns:
        float: Average RTT value.
    """
    if not responses:
        return float("inf")
    return sum(responses) / len(responses)
