#!/usr/bin/env python3

import json
import math
import folium
from folium.plugins import HeatMap
from collections import defaultdict


# ---------------- CONFIG ----------------
GRID_METERS = 5  # dimensione cella (5–10 m consigliati)
INPUT_JSON = "mapped_converted.json"
OUTPUT_HTML = "mappa_griglia_metrica.html"


# ---------------- UTILS ----------------
def ip_family(ip):
    try:
        first_octet = ip.split('.')[0]
        if first_octet in ("10", "192"):
            return first_octet
        return "ALTRO"
    except:
        return "ALTRO"


def grid_key(lat, lon, meters=GRID_METERS):
    """
    Converte lat/lon in una cella metrica approssimata.
    """
    lat_size = meters / 111_320
    lon_size = meters / (40075000 * math.cos(math.radians(lat)) / 360)
    return (
        round(lat / lat_size),
        round(lon / lon_size)
    )


# ---------------- MAIN ----------------
def crea_mappa_con_griglia_metrica(
        nome_file_input=INPUT_JSON,
        nome_file_output=OUTPUT_HTML):

    print(f"Lettura file: {nome_file_input}")

    try:
        with open(nome_file_input, 'r') as f:
            dati_gps = json.load(f)
    except Exception as e:
        print(f"Errore lettura JSON: {e}")
        return

    if not dati_gps:
        print("JSON vuoto.")
        return

    # (famiglia IP, cella) → lista punti
    grid = defaultdict(list)

    for record in dati_gps:
        try:
            lat = record["latitude"]
            lon = record["longitude"]
            ip = record["packet"]["ip"]
            fam = ip_family(ip)

            key = grid_key(lat, lon)
            grid[(fam, key)].append((lat, lon))
        except:
            continue

    # Ricostruzione per Folium: [lat, lon, peso]
    data_by_group = defaultdict(list)
    all_coords = []

    for (fam, _), pts in grid.items():
        lat = sum(p[0] for p in pts) / len(pts)
        lon = sum(p[1] for p in pts) / len(pts)
        #weight = len(pts)
        weight = min(len(pts), 15)

        data_by_group[fam].append([lat, lon, weight])
        all_coords.append((lat, lon))

    if not all_coords:
        print("Nessuna coordinata valida.")
        return

    # Centro mappa
    centro_lat = sum(c[0] for c in all_coords) / len(all_coords)
    centro_lon = sum(c[1] for c in all_coords) / len(all_coords)

    mappa = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    # --------- Layer punti (una cella = un punto) ---------
    colors = {
        "10": "red",
        "192": "blue",
        "ALTRO": "green"
    }

    for fam, points in data_by_group.items():
        fg = folium.FeatureGroup(name=f"Celle {fam}")
        color = colors.get(fam, "black")

        for lat, lon, weight in points:
            folium.CircleMarker(
                location=[lat, lon],
                radius=min(2 + weight, 10),
                color=color,
                fill=True,
                fill_opacity=0.6,
                tooltip=f"{fam} – campioni: {weight}"
            ).add_to(fg)

        fg.add_to(mappa)

    # --------- Heatmap ---------

    gradient_invertito = {
        0.0: "#f7f4f9",
        0.5: "#9e9ac8",
        1.0: "#54278f"
    }

    if "10" in data_by_group:
        fg = folium.FeatureGroup(name="Heatmap 10")
        HeatMap(
            data_by_group["10"],
            radius=7,
            blur=4,
            max_zoom=18,
            gradient=gradient_invertito,
            min_opacity=0.2
        ).add_to(fg)
        fg.add_to(mappa)

    if "192" in data_by_group:
        fg = folium.FeatureGroup(name="Heatmap 192")
        HeatMap(
            data_by_group["192"],
            radius=7,
            blur=4,
            max_zoom=18,
            gradient=gradient_invertito,
            min_opacity=0.2
        ).add_to(fg)
        fg.add_to(mappa)

    folium.LayerControl().add_to(mappa)
    mappa.save(nome_file_output)

    print(f"Mappa salvata in: {nome_file_output}")


# ---------------- RUN ----------------
if __name__ == "__main__":
    crea_mappa_con_griglia_metrica()
