import socket

import webutils.network.icmp.icmp_utils as utils
from webutils.network.icmp import Traceroute, TracerouteHop, TracerouteResponse


class DummySocket:
    def __init__(self, family, sock_type, proto):
        """
        Dummy socket to simulate send/receive behavior for traceroute tests.
        Records sent packets and returns preloaded responses on recvfrom.
        """
        self.family = family
        self.type = sock_type
        self.proto = proto
        self.timeout = None
        self.bound_addr = None
        self.opts = {}
        self.sent_packets = []
        self._responses = []

    def settimeout(self, timeout):
        """Set timeout for blocking socket operations."""
        self.timeout = timeout

    def bind(self, addr):
        """Bind the socket to the specified local address."""
        self.bound_addr = addr

    def setsockopt(self, level, optname, value):
        """Set socket options (e.g., TTL)."""
        self.opts[(level, optname)] = value

    def sendto(self, data, addr):
        """Record outgoing packets instead of sending them."""
        self.sent_packets.append((data, addr))

    def recvfrom(self, bufsize):
        """
        Return the next preloaded response or raise an exception.
        Can simulate socket.timeout or a real ICMP reply.
        """
        resp = self._responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp

    def __enter__(self):
        """Enter context manager, return self."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """Exit context manager, no special cleanup."""
        pass


def test_traceroute(monkeypatch):
    """
    Test Traceroute.start with:
    - timeout on the first hop
    - intermediate router on the second hop
    - destination reached on the third hop
    """
    # Ensure hostname resolution always returns the dummy IP
    dest_ip = "10.0.0.1"
    monkeypatch.setattr(utils, "to_ip", lambda x: dest_ip)

    # Prepare fake ICMP responses:
    # 1) socket.timeout()
    # 2) intermediate router response from 1.2.3.4
    # 3) destination response from dest_ip
    responses = [
        socket.timeout(),
        (b"dummy", ("1.2.3.4", 33436)),
        (b"dummy", (dest_ip, 33437)),
    ]
    responses_iter = iter(responses)

    def fake_socket(family, sock_type, proto):
        """Return a DummySocket that yields one response for ICMP sockets."""
        sock = DummySocket(family, sock_type, proto)
        if proto == socket.IPPROTO_ICMP:
            sock._responses = [next(responses_iter)]
        return sock

    # Patch the real socket to use our fake_socket
    monkeypatch.setattr(socket, "socket", fake_socket)

    # Run traceroute with a maximum of 3 hops
    traceroute = Traceroute("example.com", packet_size=0, timeout=1)
    resp = traceroute.start(max_hops=3, base_port=33434)

    # There should be exactly 3 hop entries
    assert len(resp) == 3

    # First hop: timeout, ip and hostname are "*", rtt == -1
    hop1 = resp[0]
    assert hop1.ttl == 1
    assert hop1.ip == "*"
    assert hop1.hostname == "*"
    assert hop1.rtt == -1.0

    # Second hop: intermediate router, IP from response, rtt >= 0
    hop2 = resp[1]
    assert hop2.ttl == 2
    assert hop2.ip == "1.2.3.4"
    assert hop2.hostname == "*"
    assert hop2.rtt >= 0

    # Third hop: destination reached, IP == dest_ip, rtt >= 0
    hop3 = resp[2]
    assert hop3.ttl == 3
    assert hop3.ip == dest_ip
    assert hop3.hostname == "*"
    assert hop3.rtt >= 0

    # Check string representation of the response
    s = str(resp)
    assert f"Traceroute to example.com, 3 hops:" in s


def test_traceroute_iterator():
    """Ensure TracerouteResponse is iterable and preserves hop order."""
    resp = TracerouteResponse()
    resp.destination = "dest"

    # Create two hop objects with different parameters
    h1 = TracerouteHop()
    h1.ttl = 1
    h1.ip = "8.8.8.8"
    h1.hostname = "dns"
    h1.rtt = 10.0

    h2 = TracerouteHop()
    h2.ttl = 2
    h2.ip = "8.8.4.4"
    h2.hostname = "dns2"
    h2.rtt = 15.0

    # Add hops to the response
    resp.add_hop(h1)
    resp.add_hop(h2)

    # Convert to list and verify the order
    hops = list(resp)
    assert hops == [h1, h2]
