import socket
import time
import pytest

from network.dns import DnsLookup, DnsResponse


def test_dns_response_init():
    """Test initial initialization of DnsResponse."""
    resp = DnsResponse('example.com')
    assert resp.domain == 'example.com'
    assert resp.addresses == []
    assert resp.time_ms == 0
    assert resp.error is None


def test_successful_lookup(monkeypatch):
    """On successful getaddrinfo, addresses list and time should be populated."""
    # Provide a fake getaddrinfo response with duplicates
    fake_results = [
        (socket.AF_INET, None, None, None, ('1.1.1.1', 0)),
        (socket.AF_INET, None, None, None, ('1.2.3.4', 0)),
        (socket.AF_INET, None, None, None, ('1.1.1.1', 0)),
    ]
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *args, **kwargs: fake_results)

    # Simulate time: start=100.0, end=100.123
    times = [100.0, 100.123]
    monkeypatch.setattr(time, 'time', lambda: times.pop(0))

    lookup = DnsLookup('example.com', timeout=5.0)
    response = lookup.start()

    assert response.domain == 'example.com'
    # addresses without duplicates
    assert set(response.addresses) == {'1.1.1.1', '1.2.3.4'}
    # time in ms
    assert response.time_ms == pytest.approx((100.123 - 100.0) * 1000)
    assert response.error is None


def test_lookup_error(monkeypatch):
    """If getaddrinfo raises an exception, error is set and addresses remain empty."""
    class FakeError(Exception):
        pass

    def fake_getaddrinfo(*args, **kwargs):
        raise FakeError('lookup failed')

    monkeypatch.setattr(socket, 'getaddrinfo', fake_getaddrinfo)

    lookup = DnsLookup('bad-domain', timeout=1.0)
    response = lookup.start()

    assert response.domain == 'bad-domain'
    assert response.addresses == []
    assert response.time_ms == 0
    assert response.error == 'lookup failed'


def test_timeout_setting(monkeypatch):
    """Check that socket.setdefaulttimeout is called with the provided timeout."""
    recorded = {}

    def fake_setdefaulttimeout(t):
        recorded['timeout'] = t

    monkeypatch.setattr(socket, 'setdefaulttimeout', fake_setdefaulttimeout)
    # To make start finish quickly, stub out getaddrinfo and time.time
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *args, **kwargs: [])
    monkeypatch.setattr(time, 'time', lambda: 0)

    lookup = DnsLookup('example.org', timeout=3.5)
    lookup.start()

    assert recorded.get('timeout') == 3.5
