import re
from pathlib import Path
def run_squad_value(kb):
    print("Starte: getSquadValue...")
     managers = {
        "2446378": "CoachLeisi",
        "165539": "Braunbär7",
        "2218524": "Julian",
        "2216931": "Timo Kramer ",
        "2202080": "Sascha187",
        "2558680": "Joel",
        "3183264": "MirkoHengst",
        "3180066": "Philipp",
        "2202088": "Robinho",
        "717710": "Vincent ",
        "2219496": "Vanilleeis23"
    }
    
        # Datei beim ersten Manager neu schreiben, danach anhängen (append)
    first = True
    for m_id, name in managers.items():
        url = f"https://api.kickbase.com/v4/leagues/2556726/managers/{m_id}/dashboard"
        response = kb.get_request(url)
        data = response.json()
        mode = "w" if first else "a"
        with open("Kaderwert.txt", mode, encoding="utf-8") as f:
            f.write(f"{name}: {data['tv']:,.0f} €\n")
        first = False
        
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
