import re
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def adjust_datetime_to_local(dt_str):
    try:
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        dt_local = dt_obj + timedelta(hours=2) # UTC zu MESZ (+2h)
        return dt_local.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return dt_str
    
def run_squad_value(kb):
    print("Starte: getSquadValue...")
    managers = {
            "2446378": "CoachLeisi",
            "165539": "Braunbär7",
            "2218524": "Julian",
            "2216931": "Timo Kramer",
            "2202080": "Sascha187",
            "2558680": "Joel",
            "3183264": "MirkoHengst",
            "3180066": "Philipp",
            "2202088": "Robinho",
            "717710": "Vincent",
            "2219496": "Vanilleeis23"
        }
    
    squad_values = []
    
    for m_id, name in managers.items():
        url = f"https://api.kickbase.com/v4/leagues/2556726/managers/{m_id}/dashboard"
        # response ist jetzt direkt das Dictionary dank der neuen get_request()
        data = kb.get_request(url) 
        
        # Ab hier kannst du direkt mit 'data' arbeiten, z.B.:
        # team_value = data.get("tv", 0)
        
        # Wert aus der API holen (meist als Float oder Int)
        value = data.get('tv', 0)
        squad_values.append((name.strip(), value))
    
    # Absteigend nach dem Kaderwert (Eintrag an Index 1 im Tuple) sortieren
    squad_values.sort(key=lambda x: x[1], reverse=True)
    
    # In die Datei schreiben (überschreibt die alte Datei komplett mit "w")
    with open("Kaderwert.txt", "w", encoding="utf-8") as f:
        f.write("Summen pro Nutzer (absteigend sortiert):\n\n")
        
        for name, value in squad_values:
            # Formatiert die Zahl mit Punkten als Tausendertrenner (z.B. 252.262.892)
            formatted_value = f"{value:,.0f}".replace(",", ".")
            f.write(f"{name} : {formatted_value} €\n")
            
    print("Kaderwerte erfolgreich sortiert und gespeichert!")
        
def run_market_players(kb):
    print("Starte: getMarketPlayers...")

    if os.path.exists("MarketPlayer.txt"):
        shutil.copyfile("MarketPlayer.txt", "MarketPlayer_old.txt")
    
    league_id = "2556726"
    url = f"https://api.kickbase.com/v4/leagues/{league_id}/market"
    
    # 1. DIREKT das Dictionary nutzen (ohne .json())
    data = kb.get_request(url)
    market_entries = []
    # Speichere die Marktspieler ab
    with open("MarketPlayer.txt", "w", encoding="utf-8") as f:
        for p in data.get("it", []):
            # 3. Wenn "username" existiert, gehört der Spieler einem Manager (nicht dem Computer)
            if p.get("i"):
                # Namen zusammensetzen
                spieler_name = p.get('n', '')
                marktwert = p.get("mv", 0)
                user_name = p.get("u")  
                try:
                    user_name = user_name.get('n')     
                except:
                    user_name = "Market" 

                # Ablaufdatum berechnen
            if user_name == "Market" and "exs" in p:
                exs = p.get("exs", 0)
                expiry_dt = datetime.now() + timedelta(seconds=exs)
                ablaufdatum = expiry_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                ablaufdatum = "Kein Ablaufdatum"

            line = f"{spieler_name} | {marktwert:,} € | {user_name} | {ablaufdatum}\n"
            market_entries.append((ablaufdatum, line))
    
    # 2. Sortieren: Markt-Spieler chronologisch nach Ablaufdatum (nächster Ablauf oben),
    #    Spieler ohne Ablaufdatum ("Kein Ablaufdatum") ganz nach unten.
    market_entries.sort(key=lambda x: (1 if x[0] == "Kein Ablaufdatum" else 0, x[0]))

    # 3. Sortierte Einträge in die MarketPlayer.txt schreiben
    with open("MarketPlayer.txt", "w", encoding="utf-8") as f:
        for _, line in market_entries:
            f.write(line)        
    print("Marktspieler erfolgreich aktualisiert!")
