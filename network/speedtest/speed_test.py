import http.client
import time
import urllib.request
from typing import ClassVar, List, Tuple


class Speedtest:
    """
    A class for measuring network download and upload speeds.
    """

    # List of units for human-readable formatting: (unit name, threshold in bps)
    UNITS: ClassVar[List[Tuple[str, float]]] = [
        ("Gbps", 1e9),
        ("Mbps", 1e6),
        ("Kbps", 1e3),
        ("bps", 1.0),
    ]

    def __init__(
            self,
            user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    ) -> None:
        """Initialize speedtest parameters.

        Args:
            user_agent: User-Agent string for HTTP requests.
        """
        self.user_agent = user_agent

    @staticmethod
    def format_speed(bps: float) -> str:
        """
        Convert bits per second to a human-readable string.
        """
        for unit, threshold in Speedtest.UNITS:
            if bps >= threshold:
                return f"{bps / threshold:.2f} {unit}"
        # Fallback (should not be reached because of 'bps' unit)
        return f"{bps:.2f} bps"

    def test_download(self, url: str, chunk_size: int = 1024 * 1024) -> float:
        """
        Measure download speed by fetching data from the given URL in chunks.
        Adds a User-Agent header to avoid 403 errors.
        Args:
            url: Request path on the server (e.g., "https://example.com/100mb.test").
            chunk_size: Size in bytes of each upload payload.
        Returns:
            Speed in bits per second (bps).
        """
        request = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent}
        )
        total_bytes = 0
        start_time = time.perf_counter()

        with urllib.request.urlopen(request) as response:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)

        elapsed = time.perf_counter() - start_time

        # convert bytes to bits per second and return
        return total_bytes * 8 / elapsed

    def test_upload(
            self,
            host: str,
            path: str,
            duration: float = 10.0,
            chunk_size: int = 1024 * 1024
    ) -> float:
        """
        Measure upload speed by sending POST requests with fixed-size payloads.
        Requires an HTTP server at host+path that accepts and discards the request body.
        Args:
            host: Server hostname (e.g., "example.com").
            path: Request path on the server (e.g., "/upload").
            duration: Total time in seconds to perform the test.
            chunk_size: Size in bytes of each upload payload.
        Returns:
            Speed in bits per second (bps).
        """
        connection = http.client.HTTPConnection(host)
        payload = b"0" * chunk_size
        total_bytes = 0
        start_time = time.perf_counter()

        while time.perf_counter() - start_time < duration:
            connection.request(
                "POST",
                path,
                body=payload,
                headers={
                    "User-Agent": self.user_agent,
                    "Content-Length": str(len(payload))
                }
            )
            response = connection.getresponse()

            # Ensure connection stays clean
            response.read()

            total_bytes += len(payload)

        elapsed = time.perf_counter() - start_time
        connection.close()
        # convert bytes to bits per second and return
        return total_bytes * 8 / elapsed
