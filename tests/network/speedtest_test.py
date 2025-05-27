from unittest.mock import MagicMock

import pytest

import webutils.network.speedtest.speed_test as speedtest
from webutils.network.speedtest import Speedtest


@pytest.mark.parametrize(
    "bps, expected",
    [
        (1e10, "10.00 Gbps"),
        (5e8, "500.00 Mbps"),
        (2e4, "20.00 Kbps"),
        (123.0, "123.00 bps"),
    ],
)
def test_format_speed(bps, expected):
    """Verify that format_speed returns correct human-readable strings."""
    assert Speedtest.format_speed(bps) == expected


def test_init_user_agent():
    """Ensure the constructor preserves the provided User-Agent string."""
    custom_ua = "CustomAgent/1.0"
    st = Speedtest(user_agent=custom_ua)
    assert st.user_agent == custom_ua


def test_download(monkeypatch):
    """
    Simulate downloading three chunks (512, 256, then end)
    and patch perf_counter to get a predictable elapsed time.
    """
    # Prepare a fake response that yields two chunks and then EOF
    chunks = [b"a" * 512, b"b" * 256, b""]
    mock_response = MagicMock()
    mock_response.read.side_effect = chunks

    class DummyContext:
        def __enter__(self):
            return mock_response

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    # Patch urlopen in the speedtest module
    monkeypatch.setattr(
        speedtest.urllib.request,
        "urlopen",
        lambda req: DummyContext(),
    )

    # Patch perf_counter so elapsed = 0.5 seconds
    perf_values = [100.0, 100.5]
    monkeypatch.setattr(
        speedtest.time,
        "perf_counter",
        lambda: perf_values.pop(0),
    )

    st = Speedtest(user_agent="TestAgent")
    speed_bps = st.test_download("https://example.com/file", chunk_size=512)

    total_bytes = 512 + 256  # bytes read
    expected_bits = total_bytes * 8  # bits read
    assert speed_bps == pytest.approx(expected_bits / 0.5)


def test_upload(monkeypatch):
    """
    Simulate a single POST upload and patch perf_counter
    to test upload speed calculation.
    """
    recorded_requests = []

    class DummyConnection:
        def __init__(self, host):
            self.host = host

        @staticmethod
        def request(method, path, body=None, headers=None):
            recorded_requests.append({
                "method": method,
                "path": path,
                "body_len": len(body or b""),
                "headers": headers,
            })

        @staticmethod
        def getresponse():
            resp = MagicMock()
            resp.read.return_value = b""  # empty response body
            return resp

        def close(self):
            pass

    # Patch HTTPConnection in the speedtest module
    monkeypatch.setattr(
        speedtest.http.client,
        "HTTPConnection",
        DummyConnection,
    )

    # Patch perf_counter to simulate:
    #   start at 0.0, check at 0.04 (enter loop), check at 0.06 (exit loop), final read at 0.06
    perf_values = [0.0, 0.04, 0.06, 0.06]
    monkeypatch.setattr(
        speedtest.time,
        "perf_counter",
        lambda: perf_values.pop(0),
    )

    st = Speedtest()
    speed_bps = st.test_upload(
        host="example.com",
        path="/upload",
        duration=0.05,
        chunk_size=512,
    )

    # Verify exactly one POST request was made
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req["method"] == "POST"
    assert req["path"] == "/upload"
    assert req["body_len"] == 512
    assert "User-Agent" in req["headers"]

    expected_bits = 512 * 8  # bits sent
    expected_speed = expected_bits / 0.06
    assert speed_bps == pytest.approx(expected_speed)
