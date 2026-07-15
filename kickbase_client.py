import requests
import json
import os
import ast
from datetime import datetime, timedelta
from collections import defaultdict
import re
from zoneinfo import ZoneInfo
from pathlib import Path

# Rekursive Funktion zum Durchsuchen und Extrahieren der Schlüssel "byr" und "type"
def extract_by_key(data, keys_to_find):
    """
    Durchsucht rekursiv das JSON-Datenobjekt nach den angegebenen Schlüsseln und gibt die entsprechenden Werte zurück.
    :param data: Die zu durchsuchende JSON-Datenstruktur.
    :param keys_to_find: Eine Liste der Schlüssel, nach denen gesucht werden soll.
    :return: Eine Liste der gefundenen Werte für die gesuchten Schlüssel.
    """
    results = []
    
    if isinstance(data, dict):
        # Wenn es sich um ein Dictionary handelt, überprüfe, ob die Schlüssel vorhanden sind
        for key, value in data.items():
            if key in keys_to_find:
                results.append((key, value))  # Speichere das Schlüssel-Wert-Paar
            # Rekursiv nach diesen Schlüsseln in den Werten suchen
            results.extend(extract_by_key(value, keys_to_find))
    
    elif isinstance(data, list):
        # Wenn es sich um eine Liste handelt, durchlaufe jedes Element
        for item in data:
            results.extend(extract_by_key(item, keys_to_find))
    
    return results

class KickbaseClient:
    
    BASE_URL = "https://api.kickbase.com/v4"

    def __init__(self):
        self.token = None

    def login(self):
        # Holt sich die Zugangsdaten sicher aus den Umgebungsvariablen von GitHub
        email = os.environ.get("KICKBASE_EMAIL")
        password = os.environ.get("KICKBASE_PASSWORD")

        if not email or not password:
            raise Exception("Fehler: KICKBASE_EMAIL oder KICKBASE_PASSWORD Umgebungsvariable fehlt!")

        url = "https://api.kickbase.com/v4/user/login"
        payload = {
                "em": email,
                "loy": False,
                "pass": password,
                "rep": {}
        }

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        self.token = data.get("tkn")
        return data

    def get_transfers(self):
        url = "https://api.kickbase.com/v4/leagues/2556726/activitiesFeed"
        start_date = 0
        max_date = 10
        # Die URL mit den Parametern 'start' und 'max' zusammenstellen
        params = {
            "start": start_date,
            "max": max_date
        }

        # API-Request ausführen
        response = requests.get(url,headers=self._headers(), params=params)

        # Prüfen, ob der Request erfolgreich war
        if response.status_code == 200:
            data = response.json()  # Antwort als JSON-Daten
        else:
            print(f"Fehler: {response.status_code}")
        # Wir gehen davon aus, dass die "activities" im JSON eine Liste von Aktivitäten sind
        activities = data.get('af', [])
        # Definiere die Schlüssel, nach denen du suchen möchtest
        keys_to_find = ['byr','slr', 'pn','trp']

        # Rufe die rekursive Funktion auf, um alle geschachtelten "byr" und "type" zu extrahieren
        arr = extract_by_key(activities, keys_to_find)
        result=[]
        i = 0
        while i < len(arr):
            # --- Spezialfall: "slr" gefolgt von "byr" ---
            if 'slr' in arr[i] and i + 3 < len(arr) and 'byr' in arr[i+1]:
                # wir brauchen pn und trp => i+2 und i+3
                byr_group = [arr[i], arr[i+2], arr[i+3]]
                slr_group = [arr[i+1], arr[i+2], arr[i+3]]
                result.append(byr_group)
                result.append(slr_group)
                # Zwei Gruppen wurden gemacht → wir springen vier Einträge weiter
                i += 4
                continue
            
            # --- Normalfall: Jede drei Elemente gruppieren ---
            if i + 2 < len(arr):
                if 'slr' in arr[i] or 'byr' in arr[i] :
                    result.append(arr[i:i+3])
                    i += 3
                else:
                    i += 2
            else:
                # restliche Elemente am Ende (falls < 3)
                result.append(arr[i:])
                break
        #Hier wird in Textdaatei geschrieben
        filename = "Transactionen.txt"

        # Datei anlegen falls sie nicht existiert
        if not os.path.exists(filename):
            open(filename, "w").close()

        # Bestehende Einträge aus Datei laden
        with open(filename, "r", encoding="utf-8") as f:
            existing_lines = {line.strip() for line in f.readlines()}
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing_lines = [l.rstrip("\n") for l in f]
        except FileNotFoundError:
            existing_lines = []

        new_lines = []

        # Neue Einträge sammeln (nur wenn nicht vorhanden)
        for entry in result:
            line = json.dumps(entry, ensure_ascii=False)

            if line not in existing_lines:
                new_lines.append(line)
                print("Neue Transaction:", line)

        # Nur neu schreiben, wenn es neue Zeilen gibt
        if new_lines:
            with open(filename, "w", encoding="utf-8") as f:
                # neue Zeilen nach oben
                f.write("\n".join(new_lines + existing_lines) + "\n")
        else:
            # optional
            # print("Keine neuen Einträge")
            pass

    def getSquadValue(self):
        #Kaderwerte bekommen
        #CoachLeisi
        url="https://api.kickbase.com/v4/leagues/2556726/managers/2446378/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "w", encoding="utf-8") as f:
            f.write(f"{"CoachLeisi"}: {data["tv"]:,.0f} €\n")
        #Braunbär7
        url="https://api.kickbase.com/v4/leagues/2556726/managers/165539/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Braunbär7"}: {data["tv"]:,.0f} €\n")
        #Julian
        url="https://api.kickbase.com/v4/leagues/2556726/managers/2218524/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Julian"}: {data["tv"]:,.0f} €\n")
        #Timo Kramer
        url="https://api.kickbase.com/v4/leagues/2556726/managers/2216931/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Timo Kramer "}: {data["tv"]:,.0f} €\n")
        #Sascha187
        url="https://api.kickbase.com/v4/leagues/2556726/managers/2202080/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Sascha187"}: {data["tv"]:,.0f} €\n")
        #Joel
        url="https://api.kickbase.com/v4/leagues/2556726/managers/2558680/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Joel"}: {data["tv"]:,.0f} €\n")
        #MirkoHengst
        url="https://api.kickbase.com/v4/leagues/2556726/managers/3183264/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"MirkoHengst"}: {data["tv"]:,.0f} €\n")
        #Philipp
        url="https://api.kickbase.com/v4/leagues/2556726/managers/3180066/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Philipp"}: {data["tv"]:,.0f} €\n")
        #Robinho
        url="https://api.kickbase.com/v4/leagues/2556726/managers/2202088/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Robinho"}: {data["tv"]:,.0f} €\n")
        #Vincent
        url="https://api.kickbase.com/v4/leagues/2556726/managers/717710/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Vincent "}: {data["tv"]:,.0f} €\n")
        #Niklas
        url="https://api.kickbase.com/v4/leagues/2556726/managers/2219496/dashboard"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("Kaderwert.txt", "a", encoding="utf-8") as f:
            f.write(f"{"Vanilleeis23"}: {data["tv"]:,.0f} €\n")
    def calculateKontostand(self):
        managers = [
        "CoachLeisi",
        "Braunbär7",
        "Julian",
        "Timo Kramer ",
        "Sascha187",
        "Joel",
        "MirkoHengst",
        "Philipp",
        "Robinho",
        "Vincent ",
        "Vanilleeis23"
        ]       
        # Startguthaben für jeden Manager
        balances = {m: 50_000_000 for m in managers}

        with open("SPG.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if ":" not in line:
                    continue

                # Name links, Werte rechts
                name, values = line.split(":", 1)
                name = name.strip()
                values = values.strip()

                # Alle Werte am Komma trennen
                parts = values.split(",")

                # Summe aller Werte in dieser Zeile
                total_add = 0
                for part in parts:
                    p = part.strip()

                    # Dezimalzeichen korrigieren
                    p = p.replace(".", "").replace(",", ".")

                    # Nur gültige Zahlen berücksichtigen
                    try:
                        total_add += float(p)
                    except ValueError:
                        print("Fehlerhafte Zahl ignoriert:", part)

                # Passender Manager → Summe addieren
                for m in managers:
                    if m.strip() == name:
                        balances[m] += total_add
                        break

        # Startdatum für Bonus
        start_date = datetime(2026, 08, 24)

        # Heutiges Datum
        today = datetime.today()

        # Anzahl der Tage berechnen
        days_passed = (today - start_date).days

        # Bonus pro Tag
        daily_bonus = 100_000

        # Gesamtsumme
        bonus_total = days_passed * daily_bonus

        # Bonus an alle Manager auszahlen
        for m in balances:
            balances[m] += bonus_total

        with open("SPG.txt", "r", encoding="utf-8") as file:
            for line in file:
                if ":" not in line:
                    continue

                name, value = line.split(":", 1)

                name = name.strip()
                value = value.strip().replace(",", ".")

                spieltagspunkte = float(value) * 1000

                if name in balances:
                    balances[name] += spieltagspunkte

        result = []  # hier kommen die eingelesenen Listen rein
        with open("Transactionen.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()               # Leerzeichen und Umbrüche entfernen
                if not line:
                    continue                      # leere Zeilen überspringen

                arr = ast.literal_eval(line)      # Text → echte Python-Liste
                result.append(arr)
        # Daten verarbeiten
        i=0
        while i<len(result):
            if 'byr'in result[i][0]:
                buyer = result[i][0][1]
                amount = result[i][2][1]
                if buyer in balances:
                    balances[buyer] -= amount
            if 'slr' in result[i][0]:
                seller = result[i][0][1]
                amount = result[i][2][1]
                if seller in balances:
                    balances[seller] += amount
            i +=1

        # Kontostände speichern
        with open("Kontostand.txt", "w", encoding="utf-8") as f:
            for manager, balance in balances.items():
                f.write(f"{manager}: {balance:,.0f} €\n")
        
        
    def calculateMaxBid(self):
        werte = {}
        with open("Kontostand.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                name, wert = line.split(":")
                name = name.strip()

                # Zahl bereinigen: Kommas raus, Euro raus
                wert = wert.replace("€", "").replace(",", "").strip()
                wert = int(wert)

                werte[name] = wert
        kontostand = werte
        werte = {}
        with open("Kaderwert.txt","r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                name, wert = line.split(":")
                name = name.strip()

                # Zahl bereinigen: Kommas raus, Euro raus
                wert = wert.replace("€", "").replace(",", "").strip()
                wert = int(wert)

                werte[name] = wert
        kaderwert = werte
        ergebnis={}
        for name in kontostand:
            if name in kaderwert:
                konto = kontostand[name]
                kader = kaderwert[name]

                max_bid = konto + int(kader * 0.33)
                ergebnis[name] = max_bid
        with open("MaxBide.txt", "w", encoding="utf-8") as out:
            out.write("Summen pro Nutzer (absteigend sortiert):\n\n")
            for name, betrag in sorted(ergebnis.items(), key=lambda x: x[1], reverse=True):
                out.write(f"{name} : {betrag:,} €\n")

    def getMarketPlayers(self):
        url="https://api.kickbase.com/v4/leagues/2556726/market"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        with open("MarketPlayer.txt", "w", encoding="utf-8") as f:
            for p in data["it"]:
                if "u" in p:
                    spieler_name = p["n"]
                    marktwert = p["mv"]
                    user_name = p["u"]["n"]
                    f.write(f"{spieler_name} | {marktwert:,} € | {user_name}\n")

    def getRealKontostand(self):
        player_values = defaultdict(int)
        output_order = [
            "CoachLeisi",
            "Braunbär7",
            "Julian",
            "Timo Kramer",
            "Sascha187",
            "Joel",
            "MirkoHengst",
            "Philipp",
            "Robinho",
            "Vincent",
            "Vanilleeis23"
        ]
        # -----------------------------
        # 1) Marktwerte pro User summieren
        # -----------------------------
        player_values = defaultdict(int)

        with open("MarketPlayer.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = [p.strip() for p in line.split("|")]
                if len(parts) != 3:
                    continue

                _, value_str, user = parts
                digits = re.sub(r"[^\d]", "", value_str)
                value = int(digits) if digits else 0

                player_values[user] += value


        # -----------------------------
        # 2) Kontostände einlesen
        # -----------------------------
        balances = {}

        with open("Kontostand.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                name, value_str = line.split(":", 1)
                name = name.strip()

                digits = re.sub(r"[^\d-]", "", value_str)
                balances[name] = int(digits)


        # -----------------------------
        # 3) Gesamtwerte berechnen
        # -----------------------------
        def fmt(n):
            return f"{n:,}".replace(",", ".")

        daten = []

        for user in output_order:
            balance = balances.get(user, 0)
            market_value = player_values.get(user, 0)
            total = balance + market_value

            daten.append((user, balance, market_value, total))

        # Nach total absteigend sortieren
        daten.sort(key=lambda x: x[3], reverse=True)

        with open("RealKontostand.txt", "w", encoding="utf-8") as f:
            for user, balance, market_value, total in daten:
                f.write(
                    f"{user} : {fmt(total)} € "
                    f"(Kontostand: {fmt(balance)} €, Spieler auf dem Markt: {fmt(market_value)} €)\n"
                )

    def CalculateKapital(self):
        FILE_1 = Path("Kaderwert.txt")
        FILE_2 = Path("Kontostand.txt")
        OUTPUT_FILE = Path("Kapital.txt")
        pattern = re.compile(r"^(.*?):\s*([-0-9\.,\s]+) €")
        totals = {}

        # ---------- Datei 1 einlesen ----------
        with FILE_1.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                m = pattern.match(line)
                if not m:
                    continue

                name, value = m.groups()
                value = value.replace(".", "").replace(" ", "").replace(",", ".")
                value = float(
                    value.replace("\xa0","").replace("\u202f","").replace(" ", "").replace(".", "").replace(",", ".")
                    )

                totals[name.strip()] = totals.get(name.strip(), 0) + value

        # ---------- Datei 2 einlesen ----------
        with FILE_2.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                m = pattern.match(line)
                if not m:
                    continue

                name, value = m.groups()
                value = value.replace(".", "").replace(" ", "").replace(",", ".")
                value = float(
                    value.replace("\xa0","").replace("\u202f","").replace(" ", "").replace(".", "").replace(",", ".")
                    )

                totals[name.strip()] = totals.get(name.strip(), 0) + value

        # ---------- Sortieren (absteigend) ----------
        sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)

        # ---------- Ergebnis in TXT speichern ----------
        with OUTPUT_FILE.open("w", encoding="utf-8") as out:
            out.write("Summen pro Nutzer (absteigend sortiert):\n\n")
            for name, value in sorted_totals:
                formatted = f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
                out.write(f"{name}: {formatted}\n")

    def UeberMarktGelaufen(self):
        url = "https://api.kickbase.com/v4/leagues/2556726/activitiesFeed"
        start_date = 0
        max_date = 100
        # Die URL mit den Parametern 'start' und 'max' zusammenstellen
        params = {
            "start": start_date,
            "max": max_date
        }

        # API-Request ausführen
        response = requests.get(url,headers=self._headers(), params=params)

        # Prüfen, ob der Request erfolgreich war
        if response.status_code == 200:
            data = response.json()  # Antwort als JSON-Daten
        else:
            print(f"Fehler: {response.status_code}")
        # Wir gehen davon aus, dass die "activities" im JSON eine Liste von Aktivitäten sind
        events = data.get('af', [])

        url="https://api.kickbase.com/v4/leagues/2556726/market"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        players= data["it"]
        output_file = "ÜberMarktGelaufen.txt"
        # 1️⃣ Existierende Einträge einlesen und als Set speichern
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

        # 2️⃣ Alle Spieler ohne 'u' sammeln
        players_without_u_set = set(p.get('n') for p in players if 'u' not in p)

        # 3️⃣ Filter: Typ-1-Einträge ohne vorherige Typ-2/BYR
        seen_players = set()
        new_entries = []

        for e in events:
            data = e.get("data", {})

            # Typ-2/BYR → Spieler merken
            if "slr" in data or "byr" in data:
                pn = data.get("pn") or data.get("ln")
                if pn:
                    seen_players.add(pn)
                continue

            # Typ-1 → ln vorhanden
            if "ln" in data:
                ln = data.get("ln")
                # nur aufnehmen, wenn noch kein Typ-2/BYR vorher und Name in players_without_u
                if ln not in seen_players and ln not in players_without_u_set:
                    dt_str = e.get("dt")
                    dt_event = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")

                    # +1 Tag
                    dt_plus_1d = dt_event + timedelta(days=1)
                    dt_plus_1d_str = dt_plus_1d.strftime("%Y-%m-%dT%H:%M:%SZ")

                    # nur hinzufügen, wenn noch nicht in TXT vorhanden
                    key = f"{ln}|{dt_plus_1d_str}"
                    if key not in existing_entries:
                        new_entries.append((dt_plus_1d, ln))
                        existing_entries.add(key)  # direkt zum Set hinzufügen

        # 4️⃣ Neue Einträge anhängen
        with open(output_file, "a", encoding="utf-8") as f:
            for dt, ln in new_entries:
                dt_str = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                f.write(f"Name: {ln} | Datum: {dt_str}\n")
                print("Über Markt gelaufen:", ln)

        # 5️⃣ Gesamte TXT nach Datum sortieren
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

        # nach Datum sortieren
        sortable.sort(key=lambda x: x[0])

        # Datei überschreiben
        with open(output_file, "w", encoding="utf-8") as f:
            for _, line in sortable:
                f.write(line)
    
    def AblaufSpieler(self):
        url="https://api.kickbase.com/v4/leagues/2556726/market"
        response = requests.get(url, headers=self._headers())
        data=response.json()
        players= data["it"]
        for e in players:
            if e['n'] == 'Palacios':
                jetzt = datetime.now()
                ablauf = jetzt + timedelta(seconds=e['exs'])

                print("Aktuelle Zeit:", jetzt.strftime('%Y-%m-%d %H:%M:%S'))
                print(e["n"],"läuft aus um:", ablauf.strftime('%Y-%m-%d %H:%M:%S'))
