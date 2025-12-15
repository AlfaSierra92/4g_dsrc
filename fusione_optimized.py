import json
from scapy.all import rdpcap
from datetime import datetime
from decimal import Decimal
import bisect

# --- CONFIGURAZIONE ---
JSON_FILE = "output.json"
PCAP_FILE = "unici.pcap"
OUTPUT_JSON = "mapped.json"
MAX_DELTA = 0.05  # 50 ms realistici

# --- CARICO I DATI ---
with open(JSON_FILE, 'r') as f:
    gps_data = json.load(f)

packets = rdpcap(PCAP_FILE)

# NORMALIZZO SUBITO I TIMESTAMP DEI PACCHETTI (FLOAT UTC)
packet_timestamps = [(float(pkt.time), pkt) for pkt in packets]
packet_timestamps.sort(key=lambda x: x[0])
packet_times = [x[0] for x in packet_timestamps]

# --- PARSE frame.time (CET → UTC) ---
def parse_frame_time(frame_time_str):
    # esempio: "Dec  5, 2025 12:39:54.284435000 CET"
    frame_time_str = frame_time_str.replace(" CET", "")
    date_part, frac = frame_time_str.split(".")
    micro = frac[:6]
    new_str = f"{date_part}.{micro}"
    dt = datetime.strptime(new_str, "%b %d, %Y %H:%M:%S.%f")
    return dt.timestamp() - 3600  # CET → UTC

# --- ORDINO GPS ---
gps_data.sort(
    key=lambda x: parse_frame_time(
        x["_source"]["layers"]["frame"]["frame.time"]
    )
)

# --- ESTRAZIONE COORDINATE ---
def extract_coords(entry):
    try:
        layers = entry["_source"]["layers"]
        ref_pos = (
            layers["its"]["cam.CamPayload_element"]
            ["cam.camParameters_element"]
            ["cam.basicContainer_element"]
            ["its.referencePosition_element"]
        )
        return int(ref_pos["its.latitude"]), int(ref_pos["its.longitude"])
    except KeyError:
        return None, None

# --- JSON SAFE ---
def make_json_safe(obj):
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(x) for x in obj]
    return str(obj)

# --- TROVA PACCHETTO PIÙ VICINO (BINARY SEARCH) ---
def find_closest_packet(ts):
    idx = bisect.bisect_left(packet_times, ts)

    candidates = []
    if idx > 0:
        candidates.append(packet_timestamps[idx - 1])
    if idx < len(packet_timestamps):
        candidates.append(packet_timestamps[idx])

    best_pkt = None
    best_delta = float("inf")

    for pkt_ts, pkt in candidates:
        delta = abs(pkt_ts - ts)
        if delta < best_delta:
            best_delta = delta
            best_pkt = pkt

    return best_pkt, best_delta

# --- MAPPING ---
mapped = []
used_packets = set()

for entry in gps_data:
    ts = parse_frame_time(entry["_source"]["layers"]["frame"]["frame.time"])
    lat, lon = extract_coords(entry)

    if lat is None:
        continue

    pkt, delta = find_closest_packet(ts)

    if pkt and delta <= MAX_DELTA and id(pkt) not in used_packets:
        mapped.append({
            "timestamp_gps": ts,
            "latitude": lat,
            "longitude": lon,
            "packet": {
                "timestamp": float(pkt.time),
                "ip": pkt["IP"].src if "IP" in pkt else None
            }
        })
        used_packets.add(id(pkt))

safe_mapped = make_json_safe(mapped)

# --- SALVO JSON ---
with open(OUTPUT_JSON, "w") as f:
    json.dump(safe_mapped, f, indent=2)

print(f"Mapping completato: {len(mapped)} entry mappate su {len(gps_data)}")
