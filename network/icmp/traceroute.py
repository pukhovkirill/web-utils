import socket
import struct
import time

from . import icmp_utils as utils
from .icmp_proto import IcmpProto


class TracerouteHop:
    """Represents a single hop in a traceroute."""

    def __init__(self, ttl: int, ip: str, hostname: str, rtt: float):
        self.__ttl = ttl
        self.__ip = ip
        self.__hostname = hostname
        self.__rtt = rtt

    def __repr__(self):
        return f"{self.__ttl:2} {self.__hostname} [{self.__ip}] {self.__rtt:.2f} ms" \
            if self.__rtt >= 0 else f"{self.__ttl:2} * * *"


class TracerouteResponse:
    """Holds the full traceroute result."""

    def __init__(self, destination: str):
        self.__destination = destination
        self.__hops: list[TracerouteHop] = []
        self.__index = 0

    def add_hop(self, hop: TracerouteHop):
        self.__hops.append(hop)

    def __iter__(self):
        self.__index = 0
        return self

    def __next__(self) -> TracerouteHop:
        if self.__index < len(self.__hops):
            hop = self.__hops[self.__index]
            self.__index += 1
            return hop
        raise StopIteration

    def __len__(self):
        return len(self.__hops)

    def __getitem__(self, index: int) -> TracerouteHop:
        return self.__hops[index]

    def __str__(self):
        lines = [f"Traceroute to {self.__destination}, {len(self.__hops)} hops:"]
        lines.extend(str(hop) for hop in self.__hops)
        return "\n".join(lines)


class Traceroute(IcmpProto):
    """Class for performing a traceroute to a destination."""

    def __init__(self, destination: str, packet_size: int, timeout: int):
        """Initialize traceroute parameters.

        Args:
            destination (str): Target address (IP or domain name).
            packet_size (int): Size of the packet payload in bytes.
            timeout (int): Timeout for each hop in seconds.
        """
        super().__init__(destination, packet_size, timeout)
        self.__response = TracerouteResponse(destination)

    def start(self, max_hops: int = 30, base_port: int = 33434) -> TracerouteResponse:
        """Start the traceroute process using UDP packets.

        Args:
            max_hops (int, optional): Maximum number of hops to trace.
            base_port (int, optional): Base destination port for UDP probes.

        Returns:
            TracerouteResponse: A response object with traceroute hops.
        """
        try:
            destination_ip = utils.to_ip(self._destination)
            print(f"Traceroute to {self._destination} [{destination_ip}], {max_hops} hops max:")

            # todo: make traceroute root-independent
            for ttl in range(1, max_hops + 1):
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as send_sock, \
                     socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as recv_sock:

                    recv_sock.settimeout(self._timeout)
                    recv_sock.bind(('', base_port))
                    send_sock.setsockopt(socket.SOL_IP, socket.IP_TTL, struct.pack('I', ttl))

                    dest_port = base_port + ttl
                    send_time = time.time()
                    send_sock.sendto(b'', (destination_ip, dest_port))

                    try:
                        data, addr = recv_sock.recvfrom(1024)
                        rtt = (time.time() - send_time) * 1000

                        self.__response.add_hop(TracerouteHop(ttl, addr[0], "", rtt))

                        if addr[0] == destination_ip:
                            break
                    except socket.timeout:
                        self.__response.add_hop(TracerouteHop(ttl, "*", "*", -1.0))

        except Exception as e:
            print(f"Error: {e}")

        return self.__response
