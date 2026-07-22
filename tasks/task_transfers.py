import os
import json
import ast
from datetime import datetime, timedelta

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

def run_transfers(kb):
    print("Starte: get_transfers...")
    url = "https://api.kickbase.com/v4/leagues/2556726/activitiesFeed"
    params = {"start": 0, "max": 10}
    response = kb.get_request(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Fehler bei Transfers: {response.status_code}")
        return

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

    filename = "Transactionen.txt"
    if not os.path.exists(filename):
        open(filename, "w").close()

    with open(filename, "r", encoding="utf-8") as f:
        existing_lines = [l.rstrip("\n") for l in f]

    new_lines = []
    for entry in result:
        line = json.dumps(entry, ensure_ascii=False)
        if line not in existing_lines:
            new_lines.append(line)
            print("Neue Transaction:", line)

    if new_lines:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines + existing_lines) + "\n")

def run_ueber_markt_gelaufen(kb):
    print("Starte: UeberMarktGelaufen...")
    
    # 1. Activities Feed holen (die letzten 100 Events)
    url_feed = "https://api.kickbase.com/v4/leagues/2556726/activitiesFeed"
    response_feed = kb.get_request(url_feed, params={"start": 0, "max": 100})
    
    # Sicherstellen, dass wir mit dem Dict arbeiten
    if hasattr(response_feed, "json"):
        data_feed = response_feed.json()
    else:
        data_feed = response_feed
        
    events = data_feed.get('af', [])

    # 2. Aktuellen Transfermarkt holen
    url_market = "https://api.kickbase.com/v4/leagues/2556726/market"
    response_market = kb.get_request(url_market)
    
    if hasattr(response_market, "json"):
        data_market = response_market.json()
    else:
        data_market = response_market
        
    market_players = data_market.get("players", [])
    
    # Set aller Spieler, die AKTUELL von Kickbase auf dem Markt sind (kein 'username' / 'u' vorhanden)
    # Wir bauen den vollen Namen "Vorname Nachname" für den Abgleich
    players_currently_on_market = set()
    for p in market_players:
        if not p.get("username"): # Wenn username leer/None ist, gehört der Spieler Kickbase
            full_name = f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
            players_currently_on_market.add(full_name)

    output_file = "ÜberMarktGelaufen.txt"

    # 3. Bereits erfasste Einträge aus der Datei einlesen (Duplikatschutz)
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
    except FileNotFoundError:
        existing_lines = []

    existing_entries = set()
    for line in existing_lines:
        if "| Datum: " in line:
            parts = line.strip().split("| Datum: ")
            name = parts[0].replace("Name: ", "").strip()
            dt = parts[1].strip()
            existing_entries.add(f"{name}|{dt}")

    # 4. Feed analysieren
    seen_purchased_or_sold = set()
    market_placements = []

    # Wir laufen chronologisch durch (älteste zuerst, falls der Feed umgekehrt sortiert ist)
    for e in reversed(events):
        data_evt = e.get("data", {})
        
        # Fall A: Spieler wurde gekauft oder verkauft -> Für "Über Markt gelaufen" gesperrt
        if "slr" in data_evt or "byr" in data_evt:
            pn = data_evt.get("pn") or data_evt.get("ln")
            if pn:
                seen_purchased_or_sold.add(pn.strip())
            continue

        # Fall B: Spieler wurde von Kickbase auf den Markt gesetzt (Typ 12)
        # Kickbase nutzt hier oft 'ln' (oder 'pn') im Event-Objekt
        if e.get("t") == 12 or "ln" in data_evt:
            ln = data_evt.get("ln") or data_evt.get("pn")
            if ln:
                ln = ln.strip()
                dt_str = e.get("dt") # Z.B. "2026-07-21T10:15:30Z"
                
                # Wenn er nicht gekauft wurde und aktuell NICHT mehr auf dem Markt ist
                if ln not in seen_purchased_or_sold and ln not in players_currently_on_market:
                    dt_event = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
                    
                    # Kickbase-Markt-Dauer beträgt exakt 24 Stunden (1 Tag)
                    dt_abgelaufen = dt_event + timedelta(days=1)
                    dt_abgelaufen_str = dt_abgelaufen.strftime("%Y-%m-%dT%H:%M:%SZ")

                    key = f"{ln}|{dt_abgelaufen_str}"
                    if key not in existing_entries:
                        market_placements.append((dt_abgelaufen, ln))
                        existing_entries.add(key)

    # 5. Neue Einträge anhängen
    with open(output_file, "a", encoding="utf-8") as f:
        for dt, ln in market_placements:
            dt_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            f.write(f"Name: {ln} | Datum: {dt_str}\n")
            print(f"Über Markt gelaufen: {ln} (am {dt_str})")

    # 6. Gesamte Datei einlesen und chronologisch nach Datum aufsteigend sortieren
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            
        sortable = []
        for line in all_lines:
            if "| Datum: " in line:
                parts = line.strip().split("| Datum: ")
                dt_str = parts[1].strip()
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
                    sortable.append((dt, line))
                except ValueError:
                    sortable.append((datetime.max, line))
            else:
                sortable.append((datetime.max, line))

        sortable.sort(key=lambda x: x[0])
        
        with open(output_file, "w", encoding="utf-8") as f:
            for _, line in sortable:
                f.write(line)
                
    except Exception as e:
        print(f"Fehler beim Sortieren der Datei: {e}")

    print("ÜberMarktGelaufen erfolgreich aktualisiert!")

def run_ablauf_spieler(kb):
    print("Starte: AblaufSpieler...")
    response = kb.get_request("https://api.kickbase.com/v4/leagues/2556726/market")
    players = response.json()["it"]
    for e in players:
        if e['n'] == 'Palacios':
            jetzt = datetime.now()
            ablauf = jetzt + timedelta(seconds=e['exs'])
            print("Aktuelle Zeit:", jetzt.strftime('%Y-%m-%d %H:%M:%S'))
            print(e["n"], "läuft aus um:", ablauf.strftime('%Y-%m-%d %H:%M:%S'))
