import socket
import struct
import time

from webutils.network.icmp import icmp_utils as utils
from webutils.network.icmp.icmp_proto import IcmpProto


class TracerouteHopBuilder:
    """Builder for TracerouteHop."""

    def __init__(self):
        self._hop = TracerouteHop()

    def with_ttl(self, ttl: int):
        self._hop.ttl = ttl
        return self

    def with_ip(self, ip: str):
        self._hop.ip = ip
        return self

    def with_hostname(self, hostname: str):
        self._hop.hostname = hostname
        return self

    def with_rtt(self, rtt: float):
        self._hop.rtt = rtt
        return self

    def build(self):
        return self._hop


class TracerouteHop:
    """Represents a single hop in a traceroute."""

    def __init__(self):
        self.ttl = 0
        self.ip = "*"
        self.hostname = "*"
        self.rtt = -1.0

    def __repr__(self):
        return f"{self.ttl:2} {self.hostname} [{self.ip}] {self.rtt:.2f} ms" \
            if self.rtt >= 0 else f"{self.ttl:2} * * *"

    @staticmethod
    def builder():
        return TracerouteHopBuilder()


class TracerouteResponse:
    """Holds the full traceroute result."""

    def __init__(self):
        self.destination = None
        self._hops: list[TracerouteHop] = []
        self._index = 0

    def add_hop(self, hop: TracerouteHop):
        self._hops.append(hop)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self) -> TracerouteHop:
        if self._index < len(self._hops):
            hop = self._hops[self._index]
            self._index += 1
            return hop
        raise StopIteration

    def __len__(self):
        return len(self._hops)

    def __getitem__(self, index: int) -> TracerouteHop:
        return self._hops[index]

    def __str__(self):
        lines = [f"Traceroute to {self.destination}, {len(self._hops)} hops:"]
        lines.extend(str(hop) for hop in self._hops)
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
        self.__response = TracerouteResponse()
        self.__response.destination = destination

    def start(self, max_hops: int = 30, base_port: int = 33434) -> TracerouteResponse:
        """Start the traceroute process using UDP packets.
           Root priviledges required.

        Args:
            max_hops (int, optional): Maximum number of hops to trace.
            base_port (int, optional): Base destination port for UDP probes.

        Returns:
            TracerouteResponse: A response object with traceroute hops.
        """
        try:
            destination_ip = utils.to_ip(self._destination)
            print(f"Traceroute to {self._destination} [{destination_ip}], {max_hops} hops max:")

            for ttl in range(1, max_hops + 1):
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as send_sock, \
                        socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as recv_sock:

                    recv_sock.settimeout(self._timeout)
                    recv_sock.bind(('', base_port))
                    send_sock.setsockopt(socket.SOL_IP, socket.IP_TTL, struct.pack('I', ttl))
                    send_sock.settimeout(self._timeout)

                    dest_port = base_port + ttl
                    send_time = time.time()
                    send_sock.sendto(b'', (destination_ip, dest_port))

                    try:
                        data, addr = recv_sock.recvfrom(1024)
                        rtt = (time.time() - send_time) * 1000

                        hop = (TracerouteHop.builder()
                               .with_ttl(ttl)
                               .with_ip(addr[0])
                               .with_rtt(rtt)
                               .build())

                        self.__response.add_hop(hop)

                        if addr[0] == destination_ip:
                            break
                    except socket.timeout:
                        hop = (TracerouteHop.builder()
                               .with_ttl(ttl)
                               .build())
                        self.__response.add_hop(hop)

        except Exception as e:
            print(f"Error: {e}")

        return self.__response
