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
    url = "https://api.kickbase.com/v4/leagues/2556726/activitiesFeed"
    response = kb.get_request(url, params={"start": 0, "max": 100})
    
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Fehler bei UeberMarktGelaufen: {response.status_code}")
        return
        
    events = data.get('af', [])

    market_res = kb.get_request("https://api.kickbase.com/v4/leagues/2556726/market")
    players = market_res.json()["it"]
    output_file = "ÜberMarktGelaufen.txt"

    try:
        with open(output_file, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
    except FileNotFoundError:
        existing_lines = []

    existing_entries = set()
    for line in existing_lines:
        parts = line.strip().split("| Datum: ")
        if len(parts) == 2:
            name = parts[0].replace("Name: ", "").strip()
            dt = parts[1].strip()
            existing_entries.add(f"{name}|{dt}")

    players_without_u_set = set(p.get('n') for p in players if 'u' not in p)
    seen_players = set()
    new_entries = []

    for e in events:
        data_evt = e.get("data", {})
        if "slr" in data_evt or "byr" in data_evt:
            pn = data_evt.get("pn") or data_evt.get("ln")
            if pn:
                seen_players.add(pn)
            continue

        if "ln" in data_evt:
            ln = data_evt.get("ln")
            if ln not in seen_players and ln not in players_without_u_set:
                dt_str = e.get("dt")
                dt_event = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
                dt_plus_1d = dt_event + timedelta(days=1)
                dt_plus_1d_str = dt_plus_1d.strftime("%Y-%m-%dT%H:%M:%SZ")

                key = f"{ln}|{dt_plus_1d_str}"
                if key not in existing_entries:
                    new_entries.append((dt_plus_1d, ln))
                    existing_entries.add(key)

    with open(output_file, "a", encoding="utf-8") as f:
        for dt, ln in new_entries:
            dt_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            f.write(f"Name: {ln} | Datum: {dt_str}\n")
            print("Über Markt gelaufen:", ln)

    with open(output_file, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    sortable = []
    for line in all_lines:
        parts = [p for p in line.split() if "T" in p and p.endswith("Z")]
        if not parts:
            sortable.append((datetime.max, line))
            continue
        dt_str = parts[0].strip()
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        sortable.append((dt, line))

    sortable.sort(key=lambda x: x[0])
    with open(output_file, "w", encoding="utf-8") as f:
        for _, line in sortable:
            f.write(line)

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
