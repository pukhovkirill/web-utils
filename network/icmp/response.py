
class Response(object):
    def __init__(self):
        self.destination = None

        self.transmitted_package_count = None
        self.received_package_count = None

        self.packet_size = None
        self.packet_loss_rate = None

        self.time = None
        self.rtt_min = None
        self.rtt_max = None
        self.rtt_avg = None
