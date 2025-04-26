from network.icmp import Traceroute
from network.icmp import Ping
from network.dns import DnsLookup
from network.speedtest import Speedtest
from qr import QRCodeGenerator

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

st = Speedtest()

# ----- Download Test -----
download_url = "http://cachefly.cachefly.net/100mb.test"
down_speed = st.test_download(download_url)
print("Download speed:", st.format_speed(down_speed))

# ----- Upload Test -----
upload_host = "filebin.net"
upload_path = "/pytest/file"
up_speed = st.test_upload(upload_host, upload_path, duration=10)
print("Upload speed:", st.format_speed(up_speed))


qr = QRCodeGenerator()
text = "https://colab.research.google.com/drive/1uKW6XjIJcdn4w-DWNT2Fck8TalxhN7fx?usp=sharing"
qr.generate(text, "out.png")
