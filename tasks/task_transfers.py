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
    # -------------------------------------------------------------------------
    RESET_SPIELER = "Ndiaye"   
    RESET_MANAGER = "Vanilleeis23"   
    RESET_TYP = "VERKAUF"       
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
    raw_results = []
    
    for e in activities:
        data_evt = e.get("data", {})
        dt_str = e.get("dt")
        
        spieler = data_evt.get("pn")
        preis = data_evt.get("trp", 0)
        
        if spieler and ("byr" in data_evt or "slr" in data_evt):
            if "slr" in data_evt and "byr" in data_evt:
                raw_results.append([{"slr": data_evt["slr"]}, {"pn": spieler}, {"trp": preis}, {"dt": dt_str}])
                raw_results.append([{"byr": data_evt["byr"]}, {"pn": spieler}, {"trp": preis}, {"dt": dt_str}])
            elif "byr" in data_evt:
                raw_results.append([{"byr": data_evt["byr"]}, {"pn": spieler}, {"trp": preis}, {"dt": dt_str}])
            elif "slr" in data_evt:
                raw_results.append([{"slr": data_evt["slr"]}, {"pn": spieler}, {"trp": preis}, {"dt": dt_str}])

    result = list(reversed(raw_results))

    # --- RESET-FILTERUNG ---
    if RESET_SPIELER is not None and RESET_MANAGER is not None and RESET_TYP is not None:
        filtered_result = []
        found_reset = False
        
        for entry in result:
            m_name, action, s_name = "", "", ""
            for item in entry:
                if isinstance(item, dict):
                    if "byr" in item:
                        m_name, action = item["byr"], "KAUF"
                    elif "slr" in item:
                        m_name, action = item["slr"], "VERKAUF"
                    elif "pn" in item:
                        s_name = item["pn"]
            
            if not found_reset:
                if s_name.lower() == RESET_SPIELER.lower() and \
                   m_name.lower() == RESET_MANAGER.lower() and \
                   action == RESET_TYP.upper():
                    print(f" [Reset] Ersten Transfer gefunden ({s_name}).")
                    found_reset = True
            
            if found_reset:
                filtered_result.append(entry)
                
        result = filtered_result
    # -----------------------

    filename = "Transactionen.txt"
    
    # 1. Existierende Einträge einlesen und parsen, damit wir inhaltlich vergleichen können
    existing_entries = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        existing_entries.append(json.loads(line))
                    except Exception:
                        pass

    # Hilfsfunktion, um einen eindeutigen Identifier für ein Event zu bauen
    def get_transfer_id(entry_list):
        mgr, spl, dt = "", "", ""
        for item in entry_list:
            if "byr" in item: mgr = f"B_{item['byr']}"
            elif "slr" in item: mgr = f"S_{item['slr']}"
            elif "pn" in item: spl = item["pn"]
            elif "dt" in item: dt = item["dt"]
        return f"{mgr}_{spl}_{dt}"

    # Erstelle ein Set von IDs, die bereits in der Datei existieren
    existing_ids = {get_transfer_id(e) for e in existing_entries}

    new_lines = []
    new_entries_to_save = []

    for entry in result:
        entry_id = get_transfer_id(entry)
        
        # HIER GEÄNDERT: Vergleich läuft jetzt über die inhaltliche ID, nicht über den rohen String
        if entry_id not in existing_ids:
            line = json.dumps(entry, ensure_ascii=False)
            new_lines.append(line)
            new_entries_to_save.append(entry)
            
            try:
                manager = ""
                action = ""
                spieler = ""
                preis = 0
                datum = "Unbekannt"
                
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
                    elif "dt" in item:
                        datum = item["dt"]
                
                preis_formatiert = f"{preis:,}".replace(",", ".")
                print(f" Neue Transaktion erfasst: [{action}] {manager} -> {spieler} für {preis_formatiert} | Datum: {datum}")
            except Exception:
                print(" Neue Transaktion erfasst (Rohdaten):", line)

    # Wenn neue Einträge da sind, schreiben wir sie zusammen mit den alten zurück
    if new_entries_to_save:
        # Wir setzen die NEUEN Einträge an den Anfang der Datei (wie in deinem Original-Code)
        all_entries = new_entries_to_save + existing_entries
        
        with open(filename, "w", encoding="utf-8") as f:
            for e in all_entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
            
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