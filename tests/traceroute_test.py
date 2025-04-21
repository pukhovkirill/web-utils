import socket

import network.icmp.icmp_utils as utils
from network.icmp import Traceroute, TracerouteHop, TracerouteResponse


class DummySocket:
    def __init__(self, family, sock_type, proto):
        self.family = family
        self.type = sock_type
        self.proto = proto
        self.timeout = None
        self.bound_addr = None
        self.opts = {}
        self.sent_packets = []
        self._responses = []

    def settimeout(self, timeout):
        self.timeout = timeout

    def bind(self, addr):
        self.bound_addr = addr

    def setsockopt(self, level, optname, value):
        self.opts[(level, optname)] = value

    def sendto(self, data, addr):
        self.sent_packets.append((data, addr))

    def recvfrom(self, bufsize):
        resp = self._responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_traceroute(monkeypatch):
    dest_ip = "10.0.0.1"
    monkeypatch.setattr(utils, "to_ip", lambda x: dest_ip)

    # Fake responses:
    # first a timeout, then an intermediate router, then destination
    responses = [
        socket.timeout(),
        (b"dummy", ("1.2.3.4", 33436)),
        (b"dummy", (dest_ip, 33437)),
    ]
    responses_iter = iter(responses)

    def fake_socket(family, sock_type, proto):
        sock = DummySocket(family, sock_type, proto)

        if proto == socket.IPPROTO_ICMP:
            sock._responses = [next(responses_iter)]
        return sock

    monkeypatch.setattr(socket, "socket", fake_socket)

    # Initialize traceroute and start
    traceroute = Traceroute("example.com", packet_size=0, timeout=1)
    resp = traceroute.start(max_hops=3, base_port=33434)

    # number of hops
    assert len(resp) == 3

    # first hop (timeout)
    hop1 = resp[0]
    assert hop1.ttl == 1
    assert hop1.ip == "*"
    assert hop1.hostname == "*"
    assert hop1.rtt == -1.0

    # second hop (intermediate router)
    hop2 = resp[1]
    assert hop2.ttl == 2
    assert hop2.ip == "1.2.3.4"
    assert hop2.hostname == "*"
    assert hop2.rtt >= 0

    # third hop (destination reached)
    hop3 = resp[2]
    assert hop3.ttl == 3
    assert hop3.ip == dest_ip
    assert hop3.hostname == "*"
    assert hop3.rtt >= 0

    s = str(resp)
    assert f"Traceroute to example.com, 3 hops:" in s


def test_traceroute_iterator():
    # Test that TracerouteResponse is iterable and preserves order
    resp = TracerouteResponse()
    resp.destination = "dest"

    h1 = TracerouteHop()
    h1.ttl = 1
    h1.ip = "8.8.8.8"
    h1.hostname = "dns"
    h1.rtt = 10.0

    h2 = TracerouteHop()
    h1.ttl = 2
    h1.ip = "8.8.4.4"
    h1.hostname = "dns2"
    h1.rtt = 15.0

    resp.add_hop(h1)
    resp.add_hop(h2)

    hops = list(resp)
    assert hops == [h1, h2]
