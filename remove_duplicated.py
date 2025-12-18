from scapy.all import rdpcap, wrpcap, IP, UDP
from ipaddress import ip_network, IPv4Address
from typing import Dict, Tuple, List

# --- CONFIGURAZIONE ---
FILE_INPUT = "mec.pcap"
FILE_OUTPUT = "unici.pcap"
SOURCE_IP = "10.0.23.211"  # L'IP sorgente specifico
FAMILY_NET = "192.168.12.0/24"  # La rete familiare, inclusa SOURCE_IP


def estrai_pacchetti_unici(input_file: str, source_ip: str, family_net: str) -> List:
    """
    Restituisce i pacchetti che contengono payload unici del singolo IP.
    """
    try:
        pacchetti = rdpcap(input_file)
    except Exception as e:
        print(f"Errore caricamento pcap: {e}")
        return []

    src_packets: Dict[bytes, float] = {}
    family_packets: Dict[bytes, float] = {}

    rete_familiare = ip_network(family_net)

    pacchetti_unici = []

    # Popolamento dei dizionari
    for pkt in pacchetti:
        if IP in pkt and UDP in pkt:
            ip_sorgente = pkt[IP].src
            payload = bytes(pkt[UDP].payload)
            timestamp = pkt.time

            if ip_sorgente == source_ip:
                src_packets[payload] = timestamp
                pacchetti_unici.append(pkt)
            elif IPv4Address(ip_sorgente) in rete_familiare:
                if payload not in family_packets:
                    family_packets[payload] = timestamp
                    pacchetti_unici.append(pkt)

    print(f"Totale pacchetti unici salvabili: {len(pacchetti_unici)}")
    return pacchetti_unici


# --- Esecuzione ---
if __name__ == "__main__":
    pacchetti_unici = estrai_pacchetti_unici(FILE_INPUT, SOURCE_IP, FAMILY_NET)

    if pacchetti_unici:
        wrpcap(FILE_OUTPUT, pacchetti_unici)
        print(f"✅ File pcap con pacchetti unici salvato in: {FILE_OUTPUT}")
    else:
        print("⚠️ Nessun pacchetto unico trovato.")
