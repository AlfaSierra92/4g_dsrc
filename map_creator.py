import json
import folium
from folium.plugins import HeatMap


def ip_family(ip):
    """Restituisce la famiglia dell'IP."""
    try:
        first_octet = ip.split('.')[0]
        if first_octet in ("10", "192"):
            return first_octet
        return "ALTRO"
    except:
        return "ALTRO"


def crea_mappa_leggera_con_heatmap(nome_file_input="mapped_converted.json",
                                   nome_file_output="mappa_leggera_heatmap.html"):

    print(f"Tentativo di lettura del file: '{nome_file_input}'...")
    try:
        with open(nome_file_input, 'r') as f:
            dati_gps = json.load(f)

        if not dati_gps:
            print("Errore: Il file JSON è vuoto o non contiene dati validi.")
            return

    except FileNotFoundError:
        print(f"Errore: Il file '{nome_file_input}' non è stato trovato.")
        return
    except json.JSONDecodeError:
        print(f"Errore: Impossibile decodificare il JSON dal file '{nome_file_input}'.")
        return

    data_by_group = {}
    all_coordinates = []

    for record in dati_gps:
        try:
            lat = record['latitude']
            lon = record['longitude']
            ip = record['packet']['ip']

            fam = ip_family(ip)

            data_by_group.setdefault(fam, []).append((lat, lon))
            all_coordinates.append((lat, lon))

        except Exception:
            continue

    if not all_coordinates:
        print("Nessuna coordinata valida trovata.")
        return

    # Colori per ogni famiglia
    colors = {
        "10": "red",
        "192": "blue",
        "ALTRO": "green"
    }

    # Centro della mappa
    centro_lat = sum(c[0] for c in all_coordinates) / len(all_coordinates)
    centro_lon = sum(c[1] for c in all_coordinates) / len(all_coordinates)

    mappa = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)

    # --- Layer dei punti ---
    for fam, coords in data_by_group.items():
        fg = folium.FeatureGroup(name=f"Famiglia {fam}")
        color = colors.get(fam, "black")

        for lat, lon in coords:
            folium.CircleMarker(
                location=[lat, lon],
                radius=3,
                color=color,
                fill=True,
                fill_opacity=0.7,
                weight=1,
                tooltip=f"Famiglia IP: {fam}"
            ).add_to(fg)

        fg.add_to(mappa)

    gradient_custom_dsrc = {
        0.8: "red",  # valore più basso
        #0.5: "yellow",
        1: "green"  # valore più alto
    }

    gradient_custom_4g = {
        0.8: "red",  # valore più basso
        #0.5: "yellow",
        1: "green"  # valore più alto
    }

    # --- Heatmap Famiglia 10 ---
    if "10" in data_by_group and data_by_group["10"]:
        heat_fg_10 = folium.FeatureGroup(name="Heatmap Famiglia 10")
        HeatMap(
            data_by_group["10"],
            radius=5,  # più piccolo → più puntiforme
            blur=3,  # poca sfocatura
            max_zoom=18,  # definizione alta
            gradient = gradient_custom_4g  # colormap invertita e fissa
        ).add_to(heat_fg_10)
        heat_fg_10.add_to(mappa)

    # --- Heatmap Famiglia 192 ---
    if "192" in data_by_group and data_by_group["192"]:
        heat_fg_192 = folium.FeatureGroup(name="Heatmap Famiglia 192")
        HeatMap(
            data_by_group["192"],
            radius=5,
            blur=3,
            max_zoom=18,
            gradient = gradient_custom_dsrc
        ).add_to(heat_fg_192)
        heat_fg_192.add_to(mappa)

    # Controllo layer
    folium.LayerControl().add_to(mappa)

    mappa.save(nome_file_output)
    print(f"Mappa salvata in '{nome_file_output}'.")


if __name__ == "__main__":
    crea_mappa_leggera_con_heatmap()
