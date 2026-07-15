import re
from pathlib import Path

# Hilfsliste der Manager (für die Zuordnung)
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

def run_squad_value(kb):
    print("Starte: getSquadValue...")
    
    # Verwende v3 statt v4, da der v4-Endpunkt für /users oft einen 404-Fehler wirft
    league_id = "2556726"
    url = f"https://api.kickbase.com/v3/leagues/{league_id}/users"
    
    response = kb.get_request(url)
    squad_values = {}
    
    if response and "users" in response:
        for user in response["users"]:
            name = user.get("name", "").strip()
            # Finde den passenden Manager in unserer Liste
            matched_manager = None
            for m in MANAGERS:
                if m.strip() == name:
                    matched_manager = m
                    break
            
            if matched_manager:
                # Hole den Team-Wert (im v3-Endpunkt heißt das Feld meist ebenfalls teamValue oder teamvalue)
                # Wir sichern uns ab und prüfen beide Schreibweisen
                team_value = user.get("teamValue") or user.get("teamvalue") or 0
                squad_values[matched_manager] = team_value
    
    # Falls die API keine Daten lieferte, füllen wir mit 0 auf
    for m in MANAGERS:
        if m not in squad_values:
            squad_values[m] = 0

    # Sortiere die Manager absteigend nach Kaderwert
    sorted_kader = sorted(squad_values.items(), key=lambda x: x[1], reverse=True)

    # Schreibt die Kaderwert.txt im einheitlichen Design
    with open("Kaderwert.txt", "w", encoding="utf-8") as f:
        f.write("Summen pro Nutzer (absteigend sortiert):\n\n")
        for manager, value in sorted_kader:
            formatted_value = f"{int(value):,}".replace(",", ".")
            f.write(f"{manager} : {formatted_value} €\n")
            
    print("Kaderwerte erfolgreich berechnet und sortiert!")
    
def run_market_players(kb):
    print("Starte: getMarketPlayers...")
    
    league_id = "2556726"
    url = f"https://api.kickbase.com/v4/leagues/{league_id}/market"
    response = kb.get_request(url)
    
    players_on_market = []
    
    if response and "players" in response:
        for player in response["players"]:
            # Nur Spieler betrachten, die von echten Managern auf den Markt gestellt wurden (username existiert)
            if "username" in player and player["username"]:
                user = player["username"].strip()
                # Vorname + Nachname des Spielers
                first_name = player.get("firstName", "")
                last_name = player.get("lastName", "")
                player_name = f"{first_name} {last_name}".strip()
                
                price = player.get("price", 0)
                formatted_price = f"{price:,}".replace(",", ".")
                
                players_on_market.append(f"{player_name} | {formatted_price} € | {user}")

    # Speichere die Marktspieler ab (hier ist keine Summen-Sortierung nötig, da es eine Liste ist)
    with open("MarketPlayer.txt", "w", encoding="utf-8") as f:
        for entry in players_on_market:
            f.write(f"{entry}\n")
            
    print("Marktspieler erfolgreich aktualisiert!")
