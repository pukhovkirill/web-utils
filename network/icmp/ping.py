import os
import socket
import struct
import time

from .response import Response
from . import ping_utils as utils


class Ping:
    """Class for performing ICMP echo requests."""

    def __init__(self, destination: str, packet_size: int, timeout: int):
        """Initialize ping parameters.

        Args:
            destination (str): Target address (IP or domain name).
            packet_size (int): Packet size in bytes.
            timeout (int): Response timeout (in seconds).
        """
        self._response = Response()
        self._response.destination = destination
        self._response.packet_size = packet_size

        self._destination = destination
        self._packet_size = packet_size
        self._timeout = timeout

    def start(self, packet_count: int = 5) -> Response:
        """Start the ping process.

        Args:
            packet_count (int, optional): Number of packets to send. Default is 5.

        Returns:
            Response: A response object containing ping statistics.
        """
        self._response.transmitted_package_count = packet_count
        self._response.received_package_count = 0
        rtt_values = []

        try:
            destination_ip = utils.to_ip(self._destination)
            print(f"Ping {self._destination} [{destination_ip}] with {self._packet_size}-byte packets")

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_ICMP) as sock:
                t = struct.pack(str("ll"), int(self._timeout), int(0))
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, t)
                start_time = time.time()
                for seq in range(packet_count):
                    packet = self._create_packet(seq)
                    sock.sendto(packet, (destination_ip, 0))
                    send_time = time.time()

                    try:
                        sock.recvfrom(1024)
                        recv_time = time.time()
                        # Convert to milliseconds
                        rtt = (recv_time - send_time) * 1000
                        rtt_values.append(rtt)

                        self._response.received_package_count += 1
                        print(f"Reply from {destination_ip}: seq={seq} time={rtt:.2f} ms")
                    except socket.timeout:
                        print(f"Packet {seq} lost.")
                    time.sleep(1)
                self._response.time = (time.time() - start_time) * 10000
        except Exception as e:
            print(f"Error: {e}")

        self._response.packet_loss_rate = (
            (1 - self._response.received_package_count / packet_count) * 100
            if packet_count > 0 else 100
        )

        if rtt_values:
            self._response.rtt_min = min(rtt_values)
            self._response.rtt_max = max(rtt_values)
            self._response.rtt_avg = sum(rtt_values) / len(rtt_values)
        else:
            self._response.rtt_min = self._response.rtt_max = self._response.rtt_avg = None

        return self._response

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
