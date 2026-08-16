import ast
import re
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Hilfsliste der Manager
MANAGERS = [
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

def run_calculate_kontostand():
    print("Starte: calculateKontostand...")
    
    # 1. Ermittle das Startguthaben basierend auf dem anfänglichen Kaderwert
    balances = {}
    initial_kader_file = Path("Anfangs_Kaderwert.txt")
    
    initial_kaderwerte = {}
    if initial_kader_file.exists():
        with initial_kader_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                name, wert_str = line.split(":", 1)
                digits = re.sub(r"[^\d]", "", wert_str)
                if digits:
                    initial_kaderwerte[name.strip()] = int(digits)

    # Berechne das jeweilige Startguthaben (150 Mio. minus Anfangs-Kaderwert)
    for m in MANAGERS:
        manager_clean = m.strip()
        if manager_clean in initial_kaderwerte:
            start_kader = initial_kaderwerte[manager_clean]
            balances[m] = 150_000_000 - start_kader
        else:
            balances[m] = 50_000_000

    # 2. Spieltagsprämien (SPG.txt) dazurechnen
    if Path("SPG.txt").exists():
        with open("SPG.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                name, values = line.split(":", 1)
                name = name.strip()
                parts = values.strip().split(",")
                total_add = 0
                for part in parts:
                    p = part.strip().replace(".", "").replace(",", ".")
                    try:
                        total_add += float(p)
                    except ValueError:
                        pass
                for m in MANAGERS:
                    if m.strip() == name:
                        balances[m] += total_add
                        break

    # 3. Bonus-Berechnung (Startdatum: 24. Aug 2026)
    start_date = datetime(2026, 8, 15)  # Gestern (15.08.2026) war Tag 1
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Vergangene Tage ab dem Starttag inklusive heute (+1)
    days = (today - start_date).days + 1

    if days <= 0:
        bonus_total = 0
    elif days <= 10:
        # Gaußsche Summenformel für die Tage 1 bis 10 (10k, 20k, ..., 100k)
        bonus_total = (days * (days + 1) // 2) * 10_000
    else:
        # 550.000 € für die ersten 10 Tage + jeweils 100.000 € für jeden weiteren Tag
        bonus_total = 550_000 + (days - 10) * 100_000

    for m in balances:
        balances[m] += bonus_total

    # Spieltagspunkte einlesen und dazurechnen
    if Path("SPG.txt").exists():
        with open("SPG.txt", "r", encoding="utf-8") as file:
            for line in file:
                if ":" not in line:
                    continue
                name, value = line.split(":", 1)
                name = name.strip()
                value = value.strip().replace(",", ".")
                try:
                    spieltagspunkte = float(value) * 1000
                    if name in balances:
                        balances[name] += spieltagspunkte
                except ValueError:
                    pass

    # 4. HIER GEÄNDERT: Transaktionen flexibel und modern verrechnen
    if Path("Transactionen.txt").exists():
        with open("Transactionen.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    # Da es valides JSON ist, nutzen wir json.loads statt ast.literal_eval
                    entry = json.loads(line)
                    
                    buyer = None
                    seller = None
                    amount = 0
                    
                    # Schleife durchsucht die Liste dynamisch nach den Keys
                    for item in entry:
                        if isinstance(item, dict):
                            if "byr" in item:
                                buyer = item["byr"]
                            elif "slr" in item:
                                seller = item["slr"]
                            elif "trp" in item:
                                amount = item["trp"]
                    
                    # Kontostände anpassen
                    if buyer and buyer in balances:
                        balances[buyer] -= amount
                    if seller and seller in balances:
                        balances[seller] += amount
                        
                except Exception as e:
                    # Falls eine Zeile mal fehlerhaft formatiert ist, überspringen
                    pass

    # Sortiert nach Kontostand absteigend
    sorted_balances = sorted(balances.items(), key=lambda x: x[1], reverse=True)

    with open("Kontostand.txt", "w", encoding="utf-8") as f:
        f.write("Summen pro Nutzer (absteigend sortiert):\n\n")
        for manager, balance in sorted_balances:
            formatted_balance = f"{int(balance):,}".replace(",", ".")
            f.write(f"{manager} : {formatted_balance} €\n")

    print("Kontostand erfolgreich berechnet!")


def run_calculate_max_bid():
    print("Starte: calculateMaxBid...")
    kontostand = {}
    if Path("Kontostand.txt").exists():
        with open("Kontostand.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                name, wert = line.split(":", 1)
                wert_clean = wert.replace("€", "").replace(".", "").replace(",", "").strip()
                if wert_clean:
                    try:
                        kontostand[name.strip()] = int(wert_clean)
                    except ValueError as e:
                        print(f"Fehler bei Kontostand-Konvertierung von {name}: {e}")

    kaderwert = {}
    if Path("Kaderwert.txt").exists():
        with open("Kaderwert.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                name, wert = line.split(":", 1)
                wert_clean = wert.replace("€", "").replace(".", "").replace(",", "").strip()
                if wert_clean:
                    try:
                        kaderwert[name.strip()] = int(wert_clean)
                    except ValueError as e:
                        print(f"Fehler bei Kaderwert-Konvertierung von {name}: {e}")

    ergebnis = {}
    for name in kontostand:
        if name in kaderwert:
            konto = kontostand[name]
            kader = kaderwert[name]
            ergebnis[name] = konto + int(kader * 0.33)

    with open("MaxBide.txt", "w", encoding="utf-8") as out:
        out.write("Summen pro Nutzer (absteigend sortiert):\n\n")
        for name, betrag in sorted(ergebnis.items(), key=lambda x: x[1], reverse=True):
            formatted_betrag = f"{int(betrag):,}".replace(",", ".")
            out.write(f"{name} : {formatted_betrag} €\n")
            
    print("Maximales Gebot erfolgreich berechnet!")


def run_real_kontostand():
    print("Starte: getRealKontostand...")
    output_order = [m.strip() for m in MANAGERS]
    player_values = defaultdict(int)

    if Path("MarketPlayer.txt").exists():
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
                player_values[user] += int(digits) if digits else 0

    balances = {}
    if Path("Kontostand.txt").exists():
        with open("Kontostand.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                name, value_str = line.split(":", 1)
                digits = re.sub(r"[^\d-]", "", value_str)
                balances[name.strip()] = int(digits) if digits else 0

    def fmt(n):
        return f"{n:,}".replace(",", ".")

    daten = []
    for user in output_order:
        balance = balances.get(user, 0)
        market_value = player_values.get(user, 0)
        total = balance + market_value
        daten.append((user, balance, market_value, total))

    daten.sort(key=lambda x: x[3], reverse=True)

    with open("RealKontostand.txt", "w", encoding="utf-8") as f:
        f.write("Summen pro Nutzer (absteigend sortiert):\n\n")
        for user, balance, market_value, total in daten:
            f.write(
                f"{user} : {fmt(total)} € "
                f"(Kontostand: {fmt(balance)} €, Spieler auf dem Markt: {fmt(market_value)} €)\n"
            )
    print("Realer Kontostand erfolgreich berechnet!")


def run_calculate_kapital():
    print("Starte: CalculateKapital...")
    FILE_1 = Path("Kaderwert.txt")
    FILE_2 = Path("Kontostand.txt")
    OUTPUT_FILE = Path("Kapital.txt")
    
    pattern = re.compile(r"^(.*?):\s*([-0-9\.,\s\xa0\u202f]+)\s*€")
    totals = {}

    for file_path in [FILE_1, FILE_2]:
        if file_path.exists():
            with file_path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    m = pattern.match(line)
                    if not m:
                        continue
                    name, value = m.groups()
                    
                    value = value.replace("\xa0", "").replace("\u202f", "").replace(" ", "")
                    value = value.replace(".", "").replace(",", "")
                    
                    try:
                        totals[name.strip()] = totals.get(name.strip(), 0) + float(value)
                    except ValueError as e:
                        print(f"Fehler beim Konvertieren von {name} ({value}): {e}")

    sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        out.write("Summen pro Nutzer (absteigend sortiert):\n\n")
        for name, value in sorted_totals:
            formatted_value = f"{int(value):,}".replace(",", ".")
            out.write(f"{name} : {formatted_value} €\n")
            
    print("Kapital erfolgreich berechnet und sortiert!")
