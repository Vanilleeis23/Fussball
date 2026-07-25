import os
import json
import ast
from datetime import datetime, timedelta, timezone

# Hilfsfunktion für die Rekursion
def extract_by_key(data, keys_to_find):
    results = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys_to_find:
                results.append((key, value))
            results.extend(extract_by_key(value, keys_to_find))
    elif isinstance(data, list):
        for item in data:
            results.extend(extract_by_key(item, keys_to_find))
    return results
    
def get_transfers(kb):
    print("Starte: get_transfers...")
    
    # -------------------------------------------------------------------------
    # START-TRANSFER NACH DEM RESET FESTLEGEN
    # Trage hier den allerersten Transfer der neuen Saison ein.
    # Wenn RESET_SPIELER = None, wird kein Transfer gefiltert (alles wird geladen).
    # -------------------------------------------------------------------------
    RESET_SPIELER = "Sander"   # Z.B. "Pavlović"
    RESET_MANAGER = "Joel"   # Z.B. "Julian"
    RESET_TYP = "VERKAUF"       # "KAUF" oder "VERKAUF"
    # -------------------------------------------------------------------------
    
    url = "https://api.kickbase.com/v4/leagues/2556726/activitiesFeed"
    params = {"start": 0, "max": 200}
    response = kb.get_request(url, params=params)
    if hasattr(response, "status_code"):
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Fehler bei Transfers: {response.status_code}")
            return
    else:
        data = response

    activities = data.get('af', [])
    
    keys_to_find = ['byr', 'slr', 'pn', 'trp']
    arr = extract_by_key(activities, keys_to_find)
    result = []
    i = 0
    while i < len(arr):
        if 'slr' in arr[i] and i + 3 < len(arr) and 'byr' in arr[i+1]:
            byr_group = [arr[i], arr[i+2], arr[i+3]]
            slr_group = [arr[i+1], arr[i+2], arr[i+3]]
            result.append(byr_group)
            result.append(slr_group)
            i += 4
            continue
        if i + 2 < len(arr):
            if 'slr' in arr[i] or 'byr' in arr[i]:
                result.append(arr[i:i+3])
                i += 3
            else:
                i += 2
        else:
            result.append(arr[i:])
            break

    # --- RESET-FILTERUNG ---
    # Da Kickbase die neuesten Transfers oben liefert, laufen wir durch die 
    # extrahierten Ergebnisse durch. Sobald wir den festgelegten "ersten Transfer" 
    # finden, behalten wir ihn noch und ignorieren alle danach folgenden (älteren) Einträge.
    if RESET_SPIELER is not None and RESET_MANAGER is not None and RESET_TYP is not None:
        filtered_result = []
        for entry in result:
            m_name, action, s_name = "", "", ""
            for item in entry:
                # HIER GEÄNDERT: item sicher entpacken, da es eine Liste/ein Tupel ist (z.B. ["slr", "Joel"])
                if len(item) == 2:
                    key, value = item[0], item[1]
                    if key == "byr":
                        m_name, action = value, "KAUF"
                    elif key == "slr":
                        m_name, action = value, "VERKAUF"
                    elif key == "pn":
                        s_name = value
            
            filtered_result.append(entry)
            
            # Wenn das der gesuchte allererste Transfer nach dem Reset war,
            # brechen wir ab, sodass ältere Transfers nicht ins System gelangen.
            if s_name.lower() == RESET_SPIELER.lower() and \
               m_name.lower() == RESET_MANAGER.lower() and \
               action == RESET_TYP.upper():
                print(f" [Reset] Ersten Transfer der neuen Saison gefunden ({s_name}). Ältere Transfers werden ignoriert.")
                break
        result = filtered_result
    # -----------------------

    filename = "Transactionen.txt"
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            pass

    with open(filename, "r", encoding="utf-8") as f:
        existing_lines = [l.rstrip("\n") for l in f]

    new_lines = []
    for entry in result:
        line = json.dumps(entry, ensure_ascii=False)
        if line not in existing_lines:
            new_lines.append(line)
            
            try:
                manager = ""
                action = ""
                spieler = ""
                preis = 0
                
                for item in entry:
                    if "byr" in item:
                        manager = item["byr"]
                        action = "KAUF"
                    elif "slr" in item:
                        manager = item["slr"]
                        action = "VERKAUF"
                    elif "pn" in item:
                        spieler = item["pn"]
                    elif "trp" in item:
                        preis = item["trp"]
                
                preis_formatiert = f"{preis:,}".replace(",", ".")
                print(f" Neue Transaktion erfasst: [{action}] {manager} -> {spieler} für {preis_formatiert}")
            except Exception:
                print(" Neue Transaktion erfasst (Rohdaten):", line)

    if new_lines:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines + existing_lines) + "\n")
            
    print(f"Transferberechnung beendet. {len(new_lines)} neue Transfers hinzugefügt.")


def run_ueber_markt_gelaufen(kb):
    print("Starte: UeberMarktGelaufen (Splitting in abgelaufene und aktive System-Spieler)...")
    
    # 1. Activities Feed holen (die letzten 200 Events)
    url_feed = "https://api.kickbase.com/v4/leagues/2556726/activitiesFeed"
    response_feed = kb.get_request(url_feed, params={"start": 0, "max": 200})
    
    if hasattr(response_feed, "json"):
        data_feed = response_feed.json()
    else:
        data_feed = response_feed
        
    events = data_feed.get('af', [])

    file_vergangenheit = "ÜberMarktGelaufen.txt"
    file_zukunft = "Ablaufdatum.txt"

    # 2. Bereits bestehende Einträge aus dem Archiv einlesen
    tracked_players = {}
    try:
        with open(file_vergangenheit, "r", encoding="utf-8") as f:
            for line in f:
                if "| Datum: " in line:
                    parts = line.strip().split("| Datum: ")
                    name = parts[0].replace("Name: ", "").strip()
                    dt_str = parts[1].strip()
                    try:
                        tracked_players[name] = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        continue
    except FileNotFoundError:
        pass

    # 3. Feed chronologisch von alt nach neu durchlaufen
    for e in reversed(events):
        data_evt = e.get("data", {})
        
        # Fall A: Spieler kommt auf den Markt
        if e.get("t") == 12:
            # Ignorieren, wenn von einem echten Manager
            if data_evt.get("ui") or data_evt.get("un"):
                continue
                
            vorname = data_evt.get("pn", "").strip()
            nachname = data_evt.get("ln", "").strip()
            full_name = f"{vorname} {nachname}".strip() if vorname else nachname
            
            if full_name:
                dt_str = e.get("dt")
                dt_event = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
                
                # Ablaufzeitpunkt berechnen
                expiration_seconds = data_evt.get("exs", 86400)
                dt_abgelaufen = dt_event + timedelta(seconds=expiration_seconds)
                
                # Temporär/Dauerhaft tracken
                tracked_players[full_name] = dt_abgelaufen

        # Fall B: Spieler wurde von einem Manager gekauft -> Fliegt sofort und dauerhaft raus
        elif "slr" in data_evt or "byr" in data_evt:
            vorname = data_evt.get("pn", "").strip()
            nachname = data_evt.get("ln", "").strip()
            full_name = f"{vorname} {nachname}".strip() if vorname else nachname
            
            if full_name and full_name in tracked_players:
                del tracked_players[full_name]

    # 4. In Vergangenheit (abgelaufen) und Zukunft (noch auf dem Markt) aufteile
    # Holt die aktuelle UTC-Zeit und entfernt die Zeitzonen-Information,
    # damit sie perfekt zu den eingelesenen Zeiten aus der Textdatei passt.
    jetzt = datetime.now(timezone.utc).replace(tzinfo=None)
    sicher_abgelaufen = {}
    aktuell_auf_markt = {}
    
    for name, dt_abgelaufen in tracked_players.items():
        if dt_abgelaufen < jetzt:
            sicher_abgelaufen[name] = dt_abgelaufen
        else:
            aktuell_auf_markt[name] = dt_abgelaufen

    # 5. Beide Listen chronologisch sortieren
    sorted_vergangenheit = sorted(sicher_abgelaufen.items(), key=lambda x: x[1])
    sorted_zukunft = sorted(aktuell_auf_markt.items(), key=lambda x: x[1])

    # 6. Archiv-Datei neu schreiben (ÜberMarktGelaufen.txt)
    with open(file_vergangenheit, "w", encoding="utf-8") as f:
        for name, dt in sorted_vergangenheit:
            dt_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            f.write(f"Name: {name} | Datum: {dt_str}\n")

    # 7. Live-Vorschau-Datei neu schreiben (Ablaufdatum.txt)
    with open(file_zukunft, "w", encoding="utf-8") as f:
        for name, dt in sorted_zukunft:
            dt_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            f.write(f"Name: {name} | Ablaufdatum: {dt_str}\n")

    print(f"Update beendet! Archiv: {len(sorted_vergangenheit)} abgelaufene Spieler | Aktuell auf dem Markt: {len(sorted_zukunft)} Spieler.")