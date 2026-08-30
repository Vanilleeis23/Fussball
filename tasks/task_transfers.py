import os
import json
import ast
from datetime import datetime, timedelta, timezone

def adjust_datetime_to_local(dt_str):
    try:
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        dt_local = dt_obj + timedelta(hours=2) # UTC zu MESZ (+2h)
        return dt_local.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return dt_str

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
    params = {"start": 0, "max": 30}
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
        dt_str = adjust_datetime_to_local(dt_str)
        spieler = data_evt.get("pn")
        preis = data_evt.get("trp", 0)
        
        # --- HIER GEÄNDERT: `preis > 0` als Filter hinzugefügt ---
        if spieler and preis > 0 and ("byr" in data_evt or "slr" in data_evt):
            if "slr" in data_evt and "byr" in data_evt:
                raw_results.append([{"slr": data_evt["slr"]}, {"pn": spieler}, {"trp": preis}, {"dt": dt_str}])
                raw_results.append([{"byr": data_evt["byr"]}, {"pn": spieler}, {"trp": preis}, {"dt": dt_str}])
            elif "byr" in data_evt:
                raw_results.append([{"byr": data_evt["byr"]}, {"pn": spieler}, {"trp": preis}, {"dt": dt_str}])
            elif "slr" in data_evt:
                raw_results.append([{"slr": data_evt["slr"]}, {"pn": spieler}, {"trp": preis}, {"dt": dt_str}])

    result = list(reversed(raw_results))

    # --- RESET-FILTERUNG (MIT FALLBACK) ---
    if RESET_SPIELER is not None and RESET_MANAGER is not None:
        # 1. Prüfen, ob der Reset-Transfer überhaupt in den abgerufenen Daten existiert
        reset_exists = False
        for entry in result:
            m_name, action, s_name = "", "", ""
            for item in entry:
                if isinstance(item, dict):
                    if "byr" in item: m_name, action = item["byr"], "KAUF"
                    elif "slr" in item: m_name, action = item["slr"], "VERKAUF"
                    elif "pn" in item: s_name = item["pn"]
            
            match_spieler = (s_name.lower() == RESET_SPIELER.lower())
            match_manager = (m_name.lower() == RESET_MANAGER.lower())
            match_typ = (action == RESET_TYP.upper()) if RESET_TYP else True
            
            if match_spieler and match_manager and match_typ:
                reset_exists = True
                break

        # 2. Wenn der Reset existiert, filtern wir ab diesem Punkt
        if reset_exists:
            filtered_result = []
            found_reset = False
            for entry in result:
                m_name, action, s_name = "", "", ""
                for item in entry:
                    if isinstance(item, dict):
                        if "byr" in item: m_name, action = item["byr"], "KAUF"
                        elif "slr" in item: m_name, action = item["slr"], "VERKAUF"
                        elif "pn" in item: s_name = item["pn"]
                
                if not found_reset:
                    match_spieler = (s_name.lower() == RESET_SPIELER.lower())
                    match_manager = (m_name.lower() == RESET_MANAGER.lower())
                    match_typ = (action == RESET_TYP.upper()) if RESET_TYP else True
                    
                    if match_spieler and match_manager and match_typ:
                        print(f" [Reset] Reset-Transfer gefunden ({s_name} von {m_name}).")
                        found_reset = True
                
                if found_reset:
                    filtered_result.append(entry)
            
            result = filtered_result
        else:
            print(" [Hinweis] Reset-Transfer nicht in den aktuellen Daten gefunden. Übernehme alle gefundenen Transfers.")
    # -------------------------------------

    filename = "Transactionen.txt"
    
    # 1. Existierende Einträge einlesen und parsen
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

    def get_transfer_id(entry_list):
        mgr, spl, dt = "", "", ""
        for item in entry_list:
            if "byr" in item: mgr = f"B_{item['byr']}"
            elif "slr" in item: mgr = f"S_{item['slr']}"
            elif "pn" in item: spl = item["pn"]
            elif "dt" in item: dt = item["dt"]
        return f"{mgr}_{spl}_{dt}"

    def get_transfer_date(entry_list):
        for item in entry_list:
            if "dt" in item:
                return item["dt"]
        return ""

    existing_ids = {get_transfer_id(e) for e in existing_entries}

    new_lines = []
    new_entries_to_save = []

    for entry in result:
        entry_id = get_transfer_id(entry)
        
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

    if new_entries_to_save:
        all_entries = new_entries_to_save + existing_entries
        all_entries.sort(key=get_transfer_date, reverse=True)
        with open(filename, "w", encoding="utf-8") as f:
            for e in all_entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
            
    print(f"Transferberechnung beendet. {len(new_lines)} neue Transfers hinzugefügt.")
    
def run_ueber_markt_gelaufen(kb):
    """
    Ermittelt abgelaufene, unverkaufte Spieler und speichert sie mit Zeitstempel in expired_players.txt.
    """
    old_market_filepath = "MarketPlayer_old.txt"
    new_market_filepath = "MarketPlayer.txt"
    transactions_filepath = "Transactionen.txt"
    output_filepath = "ÜberMarktGelaufen.txt"

    old_market = set()
    new_market = set()
    traded_players = set()

    # 1. Alten Markt-Stand einlesen
    if os.path.exists(old_market_filepath):
        with open(old_market_filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3 and parts[2].strip().lower() == "market":
                    old_market.add(parts[0].strip())

    # 2. Neuen Markt-Stand einlesen
    if os.path.exists(new_market_filepath):
        with open(new_market_filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3 and parts[2].strip().lower() == "market":
                    new_market.add(parts[0].strip())

    # 3. Transaktionen einlesen
    if os.path.exists(transactions_filepath):
        with open(transactions_filepath, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        data_list = json.loads(line_str)
                        for item in data_list:
                            if "pn" in item:
                                traded_players.add(item["pn"].strip())
                    except json.JSONDecodeError:
                        continue

    # 4. Differenz berechnen: (Alt - Neu) - Transaktionen
    expired_unbought = sorted(list((old_market - new_market) - traded_players))

    # 5. Mit Timestamp in Datei schreiben (Anhänge-Modus)
    if expired_unbought:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(output_filepath, "a", encoding="utf-8") as f:
            for player in expired_unbought:
                f.write(f"{timestamp} | {player}\n")

def run_generate_bald_auf_markt(kb):
    """
    Ermittelt Spieler, die durch Verkäufe an den Markt (aus Transactionen.txt)
    oder bisherige Markt-Angebote (MarketPlayer.txt & ÜberMarktGelaufen.txt)
    nach ca. 14 Tagen wieder auf den Markt kommen.
    
    Filtert auf ein Fenster von +/- 2 Tagen bezogen auf reference_date (Standard: heute).
    Speichert das Ergebnis sortiert in BaldAufMarkt.txt.
    """
    print("Starte: generate_bald_auf_markt...")

    reference_date = datetime.now()

    # Zeitraum: Heute - 2 Tage bis Heute + 2 Tage
    min_date = reference_date - timedelta(days=2)
    max_date = reference_date.replace(hour=23, minute=59, second=59) + timedelta(days=2)

    all_market_events = []

    # 1. Transaktionen auswerten (Nur echte Verkäufe an den Markt)
    tx_filepath = "Transactionen.txt"
    if os.path.exists(tx_filepath):
        # Erst alle Transaktionen sammeln, um Käufer/Verkäufer-Paare zu erkennen
        raw_transactions = []
        buyers_set = set() # Speichert (spieler, dt_str), um Käufe zwischen Spielern zu identifizieren

        with open(tx_filepath, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    data_list = json.loads(line_str)
                    entry = {}
                    for item in data_list:
                        entry.update(item)
                    
                    if "pn" in entry and "dt" in entry:
                        raw_transactions.append(entry)
                        if "byr" in entry:
                            # Merken, dass es für diesen Spieler zu dieser Zeit einen Käufer gab
                            buyers_set.add((entry["pn"].strip(), entry["dt"]))
                except Exception:
                    continue

        # Jetzt nur Verkäufe filtern, bei denen KEIN Käufer zum selben Zeitpunkt existiert
        for entry in raw_transactions:
            if "slr" in entry:
                player_name = entry["pn"].strip()
                dt_str = entry["dt"]

                # Wenn zu diesem Zeitpunkt KEIN Käufer eingetragen ist -> Verkauf an den Markt!
                if (player_name, dt_str) not in buyers_set:
                    dt_str_clean = dt_str.replace("Z", "")
                    try:
                        dt_obj = datetime.strptime(dt_str_clean, "%Y-%m-%dT%H:%M:%S")
                        all_market_events.append((player_name, dt_obj))
                    except ValueError:
                        continue

    # 2. ÜberMarktGelaufen.txt auswerten (Historie)
    history_filepath = "ÜberMarktGelaufen.txt"
    if os.path.exists(history_filepath):
        with open(history_filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.strip().split("|")]
                if len(parts) >= 2:
                    date_str, player_name = parts[0], parts[1]
                    try:
                        dt_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        all_market_events.append((player_name, dt_obj))
                    except ValueError:
                        continue

    # 3. Aktuellen Markt auswerten (MarketPlayer.txt - Spieler mit Seller == 'Market')
    market_filepath = "MarketPlayer.txt"
    if os.path.exists(market_filepath):
        with open(market_filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.strip().split("|")]
                if len(parts) >= 4 and parts[2].lower() == "market":
                    player_name = parts[0]
                    date_str = parts[3]
                    try:
                        dt_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        all_market_events.append((player_name, dt_obj))
                    except ValueError:
                        continue

    # 4. Projizierten Wiederkehr-Zeitpunkt berechnen (+14 Tage) & filtern (+/- 2 Tage)
    results = []
    seen_entries = set()

    for player, event_dt in all_market_events:
        return_dt = event_dt + timedelta(days=14)
        
        if min_date <= return_dt <= max_date:
            formatted_dt = return_dt.strftime("%Y-%m-%d %H:%M:%S")
            entry_str = f"{formatted_dt} | {player}"
            
            if entry_str not in seen_entries:
                seen_entries.add(entry_str)
                results.append((return_dt, entry_str))

    # Chronologisch sortieren
    results.sort(key=lambda x: x[0])

    # 5. In BaldAufMarkt.txt schreiben
    output_filepath = "BaldAufMarkt.txt"
    with open(output_filepath, "w", encoding="utf-8") as f:
        for _, entry_str in results:
            f.write(entry_str + "\n")

    print(f" [BaldAufMarkt] {len(results)} Spieler im Fenster (+/- 2 Tage) gefunden und gespeichert.")