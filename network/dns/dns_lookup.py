import socket
import time


class DnsResponse:
    """Holds DNS lookup results."""

    def __init__(self, domain: str):
        self.domain: str = domain
        self.addresses: list[str] = []
        self.time_ms: float = 0
        self.error: str | None = None


class DnsLookup:
    """Class for performing DNS resolution."""

    def __init__(self, domain: str, timeout: float = 2.0):
        """
        Args:
            domain (str): The domain name to resolve.
            timeout (float): Timeout in seconds.
        """
        self._domain = domain
        self._timeout = timeout

    def start(self) -> DnsResponse:
        """Performs the DNS lookup.

        Returns:
            DnsResponse: Lookup result.
        """
        response = DnsResponse(self._domain)
        try:
            socket.setdefaulttimeout(self._timeout)
            start = time.time()

            results = socket.getaddrinfo(self._domain, None, socket.AF_INET)

            end = time.time()
            response.time_ms = (end - start) * 1000
            response.addresses = list({sock[4][0] for sock in results})

        except Exception as e:
            response.error = str(e)

        return response
