from network.icmp import Traceroute
from network.icmp import Ping
from network.dns import DnsLookup

host = "google.com"

p = Ping(host, 64, 1)

response = p.start(10)

print(f'{response.transmitted_package_count} packets transmitted, '
      f'{response.received_package_count} received, '
      f'{response.packet_loss_rate:.0f}% packet loss, '
      f'time {response.time:.0f}ms')
print(f'rtt min/avg/max = {response.rtt_min:.3f}/{response.rtt_avg:.3f}/{response.rtt_max:.3f} ms')

host = "google.com"

t = Traceroute(host, 64, 1)

response = t.start()

for hop in response:
    print(hop)

host = "yandex.ru"

d = DnsLookup(host)

response = d.start()

for addr in response.addresses:
    print(addr)
