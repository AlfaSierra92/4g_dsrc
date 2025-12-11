import json
from scapy.all import rdpcap
from datetime import datetime
from decimal import Decimal
import time

# --- CONFIGURAZIONE ---
JSON_FILE = "output.json"
PCAP_FILE = "unici.pcap"
OUTPUT_JSON = "mapped.json"
MAX_DELTA = 0.001  # massimo delta in secondi accettabile

# --- CARICO I DATI ---
with open(JSON_FILE, 'r') as f:
    gps_data = json.load(f)  # lista di gruppi JSON

packets = rdpcap(PCAP_FILE)
packet_timestamps = [(pkt.time, pkt) for pkt in packets]

# --- FUNZIONE PER CONVERTIRE frame.time IN TIMESTAMP ---
def parse_frame_time(frame_time_str):
    # esempio: "Dec  5, 2025 12:39:54.284435000 CET"
    frame_time_str = frame_time_str.rstrip(" CET")  # rimuove CET
    # separo secondi e nanosecondi
    date_part, frac = frame_time_str.split(".")
    micro = frac[:6]  # prendo solo i primi 6 numeri per microsecondi
    new_str = f"{date_part}.{micro}"
    dt = datetime.strptime(new_str, "%b %d, %Y %H:%M:%S.%f")
    return dt.timestamp()

# --- ORDINO PER TIMESTAMP NUMERICO ---
gps_data.sort(key=lambda x: parse_frame_time(x["_source"]["layers"]["frame"]["frame.time"]))
packet_timestamps.sort(key=lambda x: x[0])

# --- FUNZIONE PER ESTRARRE COORDINATE ---
def extract_coords(entry):
    try:
        layers = entry["_source"]["layers"]
        its_cam = layers["its"]["cam.CamPayload_element"]
        ref_pos = its_cam["cam.camParameters_element"]["cam.basicContainer_element"]["its.referencePosition_element"]
        lat = int(ref_pos["its.latitude"])
        lon = int(ref_pos["its.longitude"])
        return lat, lon
    except KeyError:
        return None, None

def make_json_safe(obj):
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    if isinstance(obj, (Decimal,)):
        return float(obj)  # o: return str(obj)
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(x) for x in obj]
    return str(obj)  # fallback

# --- TROVA PACCHETTO PIÙ VICINO ---
def find_closest_packet(ts):
    closest_pkt = None
    closest_delta = float('inf')
    for pkt_ts, pkt in packet_timestamps:
        delta = abs(pkt_ts - ts)
        #print(delta)
        #print(pkt_ts, ts)
        if delta < closest_delta:
            closest_delta = delta
            closest_pkt = pkt
        elif pkt_ts > ts and delta > closest_delta:
            break
    return closest_pkt, closest_delta

# --- MAPPING ---
mapped = []
used_packets = set()

for entry in gps_data:
    ts = parse_frame_time(entry["_source"]["layers"]["frame"]["frame.time"])
    #ip_src = entry["_source"]["layers"]["ip"]["ip.src"]
    lat, lon = extract_coords(entry)
    #print(lat, lon)
    if lat is None:
        continue  # salta entry senza coordinate

    pkt, delta = find_closest_packet(ts)
    if pkt and delta <= MAX_DELTA and id(pkt) not in used_packets:
        mapped.append({
            "timestamp_gps": ts,
            "latitude": lat,
            "longitude": lon,
            "packet": {
                "timestamp": pkt.time,
                #"summary": pkt.summary()
                "ip": pkt["IP"].src
            }
        })
        print(id(pkt))
        used_packets.add(id(pkt))

safe_mapped = make_json_safe(mapped)

# --- SALVO IL JSON ---
with open(OUTPUT_JSON, 'w') as f:
    json.dump(safe_mapped, f, indent=2)

print(f"Mapping completato: {len(mapped)} entry mappate su {len(gps_data)}")
