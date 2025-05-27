import os
import struct

from webutils.network.icmp import icmp_utils as utils


class IcmpProto:
    """Class for performing ICMP echo requests."""

    def __init__(self, destination: str, packet_size: int, timeout: int):
        self._destination: str = destination
        self._packet_size: int = packet_size
        self._timeout: int = timeout

    def _create_packet(self, sequence: int) -> bytes:
        """Creates an ICMP echo request packet.

        Args:
            sequence (int): Packet sequence number.

        Returns:
            bytes: Constructed ICMP packet.
        """
        # set icmp_type -> 8 for ICMP Echo Request
        icmp_type = 8
        icmp_code = 0
        checksum = 0
        identifier = os.getpid() & 0xFFFF
        payload = bytes(self._packet_size)
        header = struct.pack("!BBHHH", icmp_type, icmp_code, checksum, identifier, sequence) + payload
        checksum = utils.calculate_checksum(header)
        header = struct.pack("!BBHHH", icmp_type, icmp_code, checksum, identifier, sequence)
        return header + payload
