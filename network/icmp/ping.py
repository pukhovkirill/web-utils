from response import Response


class Ping:

    def __init__(self, destination, packet_size, timeout):
        self.response = Response()
        self.response.destination = destination
        self.response.packet_size = packet_size

        self.destination = destination
        self.packet_size = packet_size
        self.timeout = timeout

    def start(self, packet_count=5):
        pass
