import json


def converti_file_json(input_filename, output_filename):
    """
    Legge un file JSON, converte latitude e longitude dal formato E7
    a gradi decimali e salva il risultato in un nuovo file.
    """

    FATTORE_CONVERSIONE = 10000000.0

    try:
        # 1. Caricamento dei dati dal file mapped.json
        with open(input_filename, 'r', encoding='utf-8') as f:
            dati = json.load(f)

        print(f"File '{input_filename}' caricato con successo.")

        risultati_convertiti = []

        # 2. Processamento dei record
        for record in dati:
            # Crea una copia per non sporcare i dati originali in memoria
            nuovo_record = record.copy()

            # Conversione coordinate (Assicurati che i campi esistano nel record)
            if 'latitude' in nuovo_record and 'longitude' in nuovo_record:
                nuovo_record['latitude'] = nuovo_record['latitude'] / FATTORE_CONVERSIONE
                nuovo_record['longitude'] = nuovo_record['longitude'] / FATTORE_CONVERSIONE

            risultati_convertiti.append(nuovo_record)

        # 3. Salvataggio dei risultati in un nuovo file
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(risultati_convertiti, f, indent=4)

        print(f"Conversione completata! I risultati sono in: '{output_filename}'")

    except FileNotFoundError:
        print(f"Errore: Il file '{input_filename}' non è stato trovato.")
    except json.JSONDecodeError:
        print(f"Errore: Il file '{input_filename}' non è un JSON valido.")
    except Exception as e:
        print(f"Si è verificato un errore inaspettato: {e}")


# --- Esecuzione ---
if __name__ == "__main__":
    converti_file_json('mapped.json', 'mapped_converted.json')