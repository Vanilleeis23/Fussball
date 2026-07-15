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
    url = "https://api.kickbase.com/v4/leagues/2556726/market"
    response = kb.get_request(url)
    data = response.json()
    with open("MarketPlayer.txt", "w", encoding="utf-8") as f:
        for p in data["it"]:
            if "u" in p:
                spieler_name = p["n"]
                marktwert = p["mv"]
                user_name = p["u"]["n"]
                f.write(f"{spieler_name} | {marktwert:,} € | {user_name}\n")
