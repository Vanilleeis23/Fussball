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

def run_generate_bald_auf_markt(kb, recent_days_threshold=12):
    """
    Findet jeweils den aktuellsten Referenz-Spieler für:
      1. Verkäufe an den Markt (aus Transactionen.txt bzw. Fallback ÜberMarktGelaufen.txt)
      2. Über den Markt gelaufene Spieler (aus Feed Typ 3)
    
    Gibt für beide Kategorien die Nachfolger und Vorgänger aus und prüft,
    ob die Kandidaten in den letzten `recent_days_threshold` Tagen bereits
    auf dem Markt aufgetaucht sind oder gekauft wurden.
    """
    print("Starte: generate_bald_auf_markt...")

    ref_date = datetime.now()
    min_window = ref_date - timedelta(days=20)
    max_window = ref_date - timedelta(days=12)
    recent_cutoff = ref_date - timedelta(days=recent_days_threshold)

    # 1. Feed-Aktivitäten auslesen
    feed_type_3_players = [] # (Name, Datum)
    try:
        url = "https://api.kickbase.com/v4/leagues/2556726/activitiesFeed"
        params = {"start": 0, "max": 30}
        response = kb.get_request(url, params=params)

        if hasattr(response, "status_code"):
            data = response.json() if response.status_code == 200 else {}
        else:
            data = response if isinstance(response, dict) else {}

        activities = data if isinstance(data, list) else data.get("af", [])

        for act in activities:
            if act.get("t") == 3:
                act_data = act.get("data", {})
                last_name = act_data.get("ln")
                dt_str = act.get("dt")
                if last_name and dt_str:
                    date_clean = dt_str.replace("Z", "")
                    try:
                        dt_obj = datetime.strptime(date_clean[:19], "%Y-%m-%dT%H:%M:%S")
                        feed_type_3_players.append((last_name.strip(), dt_obj))
                    except ValueError:
                        continue
    except Exception as e:
        print(f" [Hinweis] Fehler beim Auslesen des Feeds: {e}")

    # 2. Transaktionen (Verkäufe & Käufe) einlesen
    tx_events = [] # List of (dt, player_name)
    buyers_set = set()
    raw_transactions = []
    recently_bought_players = set()

    tx_filepath = "Transactionen.txt"
    if os.path.exists(tx_filepath):
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
                        player_name = entry["pn"].strip()
                        dt_str_clean = entry["dt"].replace("Z", "")
                        try:
                            dt_obj = datetime.strptime(dt_str_clean[:19], "%Y-%m-%dT%H:%M:%S")
                            if "byr" in entry:
                                buyers_set.add((player_name, entry["dt"]))
                                # Merken, wenn der Spieler kürzlich gekauft wurde
                                if dt_obj >= recent_cutoff:
                                    recently_bought_players.add(player_name.lower())
                        except ValueError:
                            pass
                except Exception:
                    continue

        for entry in raw_transactions:
            if "slr" in entry:
                player_name = entry["pn"].strip()
                dt_str = entry["dt"]

                # Nur echte Verkäufe an den Markt
                if (player_name, dt_str) not in buyers_set:
                    dt_str_clean = dt_str.replace("Z", "")
                    try:
                        dt_obj = datetime.strptime(dt_str_clean[:19], "%Y-%m-%dT%H:%M:%S")
                        tx_events.append((dt_obj, player_name))
                    except ValueError:
                        continue

    tx_events.sort(key=lambda x: x[0])

    # 3. ÜberMarktGelaufen.txt & Aktuellen Markt (MarketPlayer.txt) einlesen
    market_history_events = [] # List of (dt, player_name)
    recently_on_market_players = set()

    history_filepath = "ÜberMarktGelaufen.txt"
    if os.path.exists(history_filepath):
        with open(history_filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.strip().split("|")]
                if len(parts) >= 2:
                    date_str, player_name = parts[0], parts[1]
                    try:
                        dt_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        market_history_events.append((dt_obj, player_name))
                        # Prüfen, ob der Spieler kürzlich über den Markt gelaufen ist
                        if dt_obj >= recent_cutoff:
                            recently_on_market_players.add(player_name.lower())
                    except ValueError:
                        continue

    market_history_events.sort(key=lambda x: x[0])

    # Aktuell auf dem Markt befindliche Spieler auslesen
    market_filepath = "MarketPlayer.txt"
    if os.path.exists(market_filepath):
        with open(market_filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.strip().split("|")]
                if len(parts) >= 1:
                    recently_on_market_players.add(parts[0].lower())

    # ---------------------------------------------------------
    # SUCHE 1: Verkaufs-Referenzspieler bestimmen (12-20 Tage Fenster)
    # ---------------------------------------------------------
    ref_sold_player = None
    ref_sold_source = None

    for name, dt in feed_type_3_players:
        for tx_dt, tx_name in reversed(tx_events):
            if name.lower() == tx_name.lower() and min_window <= tx_dt <= max_window:
                ref_sold_player = (tx_name, tx_dt)
                ref_sold_source = "Transactionen.txt"
                break
        if ref_sold_player:
            break

    if not ref_sold_player:
        for dt, name in reversed(market_history_events):
            if min_window <= dt <= max_window:
                ref_sold_player = (name, dt)
                ref_sold_source = "ÜberMarktGelaufen.txt (Fallback)"
                break

    # ---------------------------------------------------------
    # SUCHE 2: Markt-Referenzspieler bestimmen (Über Markt gelaufen)
    # ---------------------------------------------------------
    ref_market_player = feed_type_3_players[0] if feed_type_3_players else None

    # ---------------------------------------------------------
    # AUSGABE GENERIEREN (Nachbarn ermitteln & filtern)
    # ---------------------------------------------------------
    output_lines = []

    def append_neighbors(player_tuple, event_list, category_title, source_name):
        if not player_tuple or not event_list:
            output_lines.append(f"=== {category_title}: Keinen passenden Spieler gefunden. ===\n")
            return

        p_name, p_dt = player_tuple
        matching_indices = [
            i for i, ev in enumerate(event_list)
            if p_name.lower() == ev[1].lower()
        ]

        if not matching_indices:
            output_lines.append(f"=== {category_title}: '{p_name}' nicht in {source_name} gefunden. ===\n")
            return

        idx = matching_indices[-1]
        total = len(event_list)

        output_lines.append("==================================================")
        output_lines.append(f" {category_title}")
        output_lines.append(f" REFERENZ: {p_name} ({p_dt.strftime('%Y-%m-%d %H:%M:%S')}) [{source_name}]")
        output_lines.append("==================================================")

        # 10 Davor
        start_before = max(0, idx - 10)
        output_lines.append("\n--- 10 Spieler davor (historisch) ---")
        for i in range(start_before, idx):
            dt, name = event_list[i]
            output_lines.append(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')} | {name}")

        # 10 Danach mit Ausfilterungs-Hinweisen
        end_after = min(total, idx + 11)
        output_lines.append(f"\n--- 10 Spieler danach (NÄCHSTE KANDIDATEN - gefiltert auf letzte {recent_days_threshold} Tage) ---")
        for i in range(idx + 1, end_after):
            dt, name = event_list[i]
            name_lower = name.lower()
            
            flags = []
            if name_lower in recently_on_market_players:
                flags.append("BEREITS AUF DEM MARKT / KÜRZLICH GELAUFEN")
            if name_lower in recently_bought_players:
                flags.append("KÜRZLICH GEKAUFT")

            flag_str = f" <-- SKIP ({', '.join(flags)})" if flags else ""
            output_lines.append(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')} | {name}{flag_str}")
        output_lines.append("\n")

    # 1. Nachbarn für Verkaufs-Referenz ausgeben
    if ref_sold_player:
        source_list = tx_events if "Transactionen" in ref_sold_source else market_history_events
        append_neighbors(ref_sold_player, source_list, "VERKAUF AN DEN MARKT (VERLAUF)", ref_sold_source)

    # 2. Nachbarn für Markt-Durchlauf-Referenz ausgeben
    if ref_market_player:
        append_neighbors(ref_market_player, market_history_events, "ÜBER DEN MARKT GELAUFEN (VERLAUF)", "ÜberMarktGelaufen.txt")

    # Ergebnis in Datei schreiben
    output_filepath = "BaldAufMarkt.txt"
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f" [BaldAufMarkt] Analyse abgeschlossen und in '{output_filepath}' gespeichert.")