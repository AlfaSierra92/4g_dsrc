from scapy.all import rdpcap, IP, UDP
from ipaddress import ip_network
from matplotlib import pyplot as plt
import scienceplots

PCAP_FILE = "test_no_downlink.pcap"

SOURCE_IP = "10.0.23.211"
FAMILY_NET = ip_network("192.168.12.0/24")

FONT_SIZE = 16

packets = rdpcap(PCAP_FILE)

src_packets = {}
family_packets = {}

time_deltas = []

# 1. Separazione pacchetti
for pkt in packets:
    if IP in pkt and UDP in pkt:
        ip = pkt[IP].src
        payload = bytes(pkt[UDP].payload)
        timestamp = pkt.time

        if ip == SOURCE_IP:
            src_packets[payload] = timestamp

        elif ip_network(pkt[IP].src + "/32").subnet_of(FAMILY_NET):
            if payload in family_packets.keys():
                continue
            family_packets[payload] = timestamp

for payload in src_packets.keys():
    if payload in family_packets.keys():
        if (src_packets[payload] - family_packets[payload]) * 1000 < 300.0:
            time_deltas.append((src_packets[payload] - family_packets[payload]) * 1000)

list_zero = [0] * len(time_deltas)

with open("time_deltas.txt", "w") as f:
    for delta in time_deltas:
        f.write(f"{delta}\n")

plt.style.use(['science', 'ieee', 'no-latex'])
plt.figure(figsize=(12, 6))

plt.plot(time_deltas, marker='.', linestyle='', color='blue', alpha=0.8, label='Time-Delta', rasterized=True, markersize=5)
plt.plot(list_zero, marker='.', linestyle='', color='red', alpha=0.8, label='', rasterized=True, markersize=5)
plt.xlabel('N. packets', fontsize=FONT_SIZE)
plt.ylabel('Time (ms)', fontsize=FONT_SIZE)

plt.legend(fontsize=FONT_SIZE)
plt.xticks(fontsize=FONT_SIZE)
plt.yticks(fontsize=FONT_SIZE)
plt.grid(True)

plt.savefig('time-deltas_full.svg', format="svg", dpi=300)
plt.show()
