import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Liga-ID & Konfiguration
LEAGUE_ID = "2556726"
BASE_URL = "https://api.kickbase.com"

# Statische Manager-Liste
MANAGER_IDS = {
    "2446378": "CoachLeisi",
    "165539": "Braunbär7",
    "2218524": "Julian",
    "2216931": "Timo Kramer",
    "2202080": "Sascha187",
    "2558680": "Joel",
    "3183264": "MirkoHengst",
    "3180066": "Philipp",
    "2202088": "404",
    "717710": "Vincent",
    "2219496": "Vanilleeis23"
}

# Mapping der offiziellen Kickbase Team-IDs zu den echten Vereinsnamen
TEAM_NAMES = {
    2: "Bayern München",
    3: "Borussia Dortmund",
    4: "Eintracht Frankfurt",
    5: "SC Freiburg",
    6: "Hamburger SV",
    7: "Bayer Leverkusen",
    8: "FC Schalke 04",  
    9: "VfB Stuttgart",   
    10: "Werder Bremen",       
    13: "FC Augsburg",
    14: "TSG 1899 Hoffenheim",
    15: "VFL Borussia Mönchengladbach",
    18: "1. FSV Mainz 05",
    28: "1. FC Köln",     
    29: "SC Paderborn 07",       
    40: "1. FC Union Berlin",
    43: "RB Leipzig",  
    77: "SV 07 Elversberg"
}

# Nutzt die Keys des Mappings direkt als Schleifen-Basis
BUNDESLIGA_TEAM_IDS = list(TEAM_NAMES.keys())

# Festgelegte Reihenfolge nach Tabellenplatzierung der letzten Saison + Sonderwünsche am Ende
TEAM_ORDER = [
    "Bayern München",
    "Borussia Dortmund",
    "RB Leipzig",
    "VfB Stuttgart",
    "TSG 1899 Hoffenheim",
    "Bayer Leverkusen",
    "SC Freiburg",
    "Eintracht Frankfurt",
    "FC Augsburg",
    "1. FSV Mainz 05",
    "1. FC Union Berlin",
    "VFL Borussia Mönchengladbach",
    "Hamburger SV",
    "1. FC Köln",     
    "Werder Bremen",
    "FC Schalke 04",     # Platz 16
    "SV 07 Elversberg",  # Platz 17
    "SC Paderborn 07"    # Ganz am Ende (Platz 18)
]

def fetch_owned_players(kb):
    """Holt alle vergebenen Spieler aus den Manager-Dashboards."""
    owned_players = {}
    print("Frage Manager-Dashboards ab...")
    
    for m_id, m_name in MANAGER_IDS.items():
        url = f"{BASE_URL}/v4/leagues/{LEAGUE_ID}/managers/{m_id}/squad"
        try:
            data = kb.get_request(url)
            players_data = data.get("it", [])
            for p in players_data:
                p_id = p.get("pi")
                if p_id:
                    owned_players[p_id] = m_name
        except Exception as e:
            print(f"Fehler bei Manager {m_name} ({m_id}): {e}")
            
    return owned_players


def fetch_all_bundesliga_players(kb):
    """Holt die komplette Spieler-Datenbasis aller 18 Vereine mit echten Teamnamen."""
    all_players = []
    pos_mapping = {1: "Torwart", 2: "Abwehr", 3: "Mittelfeld", 4: "Sturm"}
    
    for team_id in BUNDESLIGA_TEAM_IDS:
        url = f"{BASE_URL}/v4/leagues/{LEAGUE_ID}/teams/{team_id}/teamprofile"
        try:
            data = kb.get_request(url)
            players_data = data.get("it", [])
            for p in players_data:
                p_id = p.get("i")
                if not p_id:
                    continue
                    
                pos_raw = p.get("pos", "Unbekannt")
                position = pos_mapping.get(pos_raw, pos_raw)
                
                team_id_raw = p.get("tid")
                try:
                    team_name = TEAM_NAMES.get(int(team_id_raw), f"Team {team_id_raw}")
                except (ValueError, TypeError):
                    team_name = f"Team {team_id_raw}"

                all_players.append({
                    "id": p_id,
                    "lastName": p.get("n", ""),
                    "position": position,
                    "marketValue": p.get("mv", 0),
                    "AveragePoints": p.get("ap", 0),
                    "teamName": team_name,
                    "status": p.get("st", 0),      # Neu aufgenommen
                    "probability": p.get("prob", 0) # Neu aufgenommen
                })
        except Exception as e:
            print(f"Fehler bei Team ID {team_id}: {e}")  
    return all_players

def run_generate_playerlist_html(kb):
    """
    Generiert die spielerliste.html mit erweiterten Filteroptionen für
    Teams, Positionen, Startelf-Wahrscheinlichkeiten und medizinische Stati.
    Inklusive farblicher Hervorhebung der Top-Teams im Dropdown.
    """
    all_players = fetch_all_bundesliga_players(kb)
    owned_players = fetch_owned_players(kb)
    
    short_pos_mapping = {
        "Torwart": "TW",
        "Abwehr": "ABW",
        "Mittelfeld": "MF",
        "Sturm": "ANG"
    }
    
    gefundene_stati = set()
    gefundene_wahrscheinlichkeiten = set()
    
    # 1. Besitzer-Attribut anreichern
    for player in all_players:
        player_id = player.get("id")
        if player_id in owned_players:
            player["besitzer"] = owned_players[player_id]
        else:
            player["besitzer"] = "Frei"

    # 2. Sortierung nach Marktwert absteigend
    all_players.sort(key=lambda x: x.get("marketValue") if x.get("marketValue") is not None else 0, reverse=True)
    
    # 3. Aktuelles Datum für den Header
    tz_berlin = ZoneInfo("Europe/Berlin")
    aktuelles_datum = datetime.now(tz_berlin).strftime("%d.%m.%Y um %H:%M Uhr")

    # 4. Dropdown für Teams bauen (MIT FARBLICHER HINTERLEGUNG)
    unique_teams_in_data = set(TEAM_NAMES.values())
    sorted_dropdown_teams = sorted(
        list(unique_teams_in_data),
        key=lambda t: TEAM_ORDER.index(t) if t in TEAM_ORDER else 999
    )

    dropdown_options_html = ""
    for team in sorted_dropdown_teams:
        bg_class = ""
        # Farbkriterien für die Top-Teams
        if team in ["Bayern München", "Borussia Dortmund", "RB Leipzig", "VfB Stuttgart"]:
            bg_class = "team-highlight-blue"
        elif team in ["SC Freiburg", "TSG 1899 Hoffenheim", "Bayer Leverkusen"]:
            bg_class = "team-highlight-orange"

        dropdown_options_html += f"""
        <label class="dropdown-item {bg_class}">
            <input type="checkbox" value="{team}" onchange="filterTable()"> {team}
        </label>"""

    # 5. Tabellenzeilen generieren
    player_rows_html = ""
    
    if not all_players:
        player_rows_html = """
        <tr>
            <td colspan="6" style="text-align: center; color: #94a3b8; font-style: italic; padding: 30px;">
                Keine Spielerdaten gefunden.
            </td>
        </tr>"""
    else:
        for p in all_players:
            name = p.get("lastName", "")
            team = p.get("teamName", "Verein")
            ap = p.get("AveragePoints", 0)
            mv = p.get("marketValue", 0)
            besitzer = p.get("besitzer", "Frei")
            
            status_raw = p.get("status")
            prob_raw = p.get("probability")
            
            status_val = "unknown" if status_raw is None else str(status_raw)
            prob_val = "0" if prob_raw is None else str(prob_raw)
            
            if status_raw is not None: gefundene_stati.add(status_raw)
            if prob_raw is not None: gefundene_wahrscheinlichkeiten.add(prob_raw)
            
            mv_formatiert = f"{mv:,}".replace(",", ".") + " €"
            ap_formatiert = f"{ap:,}".replace(",", ".")
            
            pos_full = p.get("position", "")
            pos_short = short_pos_mapping.get(pos_full, pos_full)
            
            pos_class = "pos-tw" if pos_full == "Torwart" else "pos-abw" if pos_full == "Abwehr" else "pos-mf" if pos_full == "Mittelfeld" else "pos-st"
            pos_td_html = f'<td data-pos="{pos_short}"><span class="pos-badge {pos_class}">{pos_short}</span></td>' if pos_short else '<td data-pos="">-</td>'
            
            # === STATUS-LOGIK ===
            if status_raw == 0:
                status_html = '<span class="indicator-circle status-fit" title="Fit">✔️</span>'
            elif status_raw == 2:
                status_html = '<span class="indicator-circle status-injured" title="Angeschlagen">🩹</span>'
            elif status_raw == 4:
                status_html = '<span class="indicator-circle status-training" title="Im Aufbautraining">🏋️</span>'
            elif status_raw == 8:
                status_html = '<span class="indicator-circle status-suspended" title="Gesperrt">🟥</span>'
            elif status_raw == 256:
                status_html = '<span class="indicator-circle status-away" title="Abwesend">⏳</span>'
            elif status_raw == 1 or status_raw is None:
                status_html = '<span class="indicator-circle status-out" title="Verletzt / Ausfall">❌</span>'
                status_val = "1"
            else:
                status_html = f'<span class="indicator-circle status-alert" title="Unbekannter Status-Code ({status_raw})">❓</span>'
                
            # === PROBABILITY LOGIK ===
            if prob_raw == 1:
                prob_html = '<span class="indicator-circle prob-safe" title="Sicher Startelf">⭐</span>'
            elif prob_raw == 2:
                prob_html = '<span class="indicator-circle prob-high" title="Sehr Wahrscheinlich">✔️</span>'
            elif prob_raw == 3:
                prob_html = '<span class="indicator-circle prob-medium" title="Möglich / Rotationsgefahr">❓</span>'
            elif prob_raw == 4:
                prob_html = '<span class="indicator-circle prob-low" title="Unwahrscheinlich">⚠️</span>'
            elif prob_raw == 5:
                prob_html = '<span class="indicator-circle prob-none" title="Ausfall / Keine Startelf">✖️</span>'
            else:
                prob_html = ''

            if besitzer == "Frei":
                besitzer_style = "color: #64748b; font-style: italic;"
            else:
                besitzer_style = "color: #f1f5f9; font-weight: 600;"

            player_rows_html += f"""
            <tr data-prob="{prob_val}" data-status="{status_val}">
                <td style="text-align: left; font-weight: 500; color: #fff;">
                    <div class="player-name-container">
                        <span class="player-name-text">{name}</span>
                        {prob_html}
                        {status_html}
                    </div>
                </td>
                {pos_td_html}
                <td style="text-align: left; color: #94a3b8;">{team}</td>
                <td class="number" data-val="{ap}" style="color: #38bdf8;">{ap_formatiert}</td>
                <td class="number" data-val="{mv}" style="color: #4ade80;">{mv_formatiert}</td>
                <td style="{besitzer_style}">{besitzer}</td>
            </tr>"""

    # 6. HTML-Dokument zusammenbauen
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spielerliste Übersicht</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 30px;
            border-bottom: 1px solid #334155;
            padding-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 15px;
        }}
        h1 {{ margin: 0; color: #38bdf8; font-size: 2em; }}
        .stand {{ font-size: 0.85em; color: #64748b; margin-top: 5px; }}
        .nav-link {{
            color: #38bdf8;
            text-decoration: none;
            font-size: 0.95em;
            font-weight: 500;
            border: 1px solid #38bdf8;
            padding: 8px 16px;
            border-radius: 6px;
            transition: all 0.2s ease;
            white-space: nowrap;
        }}
        .nav-link:hover {{
            background-color: #38bdf8;
            color: #0f172a;
        }}
        .card {{
            background-color: #1e293b;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #334155;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
        }}
        
        .filter-container {{
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .search-input {{
            background: #0f172a;
            border: 1px solid #334155;
            color: #fff;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 0.95em;
            width: 100%;
            max-width: 320px;
        }}
        .search-input:focus {{
            outline: none;
            border-color: #38bdf8;
        }}

        .dropdown {{
            position: relative;
            display: inline-block;
        }}
        .dropdown-button {{
            background: #0f172a;
            border: 1px solid #334155;
            color: #fff;
            padding: 12px 14px;
            border-radius: 6px;
            font-size: 0.9em;
            cursor: pointer;
            min-width: 170px;
            text-align: left;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .dropdown-button:focus {{
            border-color: #38bdf8;
        }}
        .dropdown-content {{
            display: none;
            position: absolute;
            background-color: #1e293b;
            min-width: 240px;
            box-shadow: 0px 8px 16px rgba(0,0,0,0.5);
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 10px;
            z-index: 10;
            max-height: 400px;
            overflow-y: auto;
            margin-top: 5px;
        }}
        .dropdown-content.show {{
            display: block;
        }}
        .dropdown-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 10px;
            color: #f8fafc;
            cursor: pointer;
            border-radius: 4px;
            font-size: 0.9em;
            margin-bottom: 2px;
        }}
        .dropdown-item:hover {{
            background-color: #273549;
        }}

        /* DA SIND SIE WIEDER: CSS-Klassen für Highlight-Teams im Dropdown */
        .team-highlight-blue {{
            background-color: rgba(56, 189, 248, 0.08) !important;
            border-left: 3px solid #38bdf8;
        }}
        .team-highlight-orange {{
            background-color: rgba(249, 115, 22, 0.08) !important;
            border-left: 3px solid #f97316;
        }}

        .dropdown-item input {{
            cursor: pointer;
            accent-color: #38bdf8;
        }}

        table {{ width: 100%; border-collapse: collapse; font-size: 0.95em; margin-top: 10px; }}
        th {{
            background-color: #1e293b;
            color: #94a3b8;
            padding: 12px 14px;
            font-weight: 600;
            border-bottom: 2px solid #334155;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 0.5px;
        }}
        th.sortable {{
            cursor: pointer;
            user-select: none;
        }}
        th.sortable:hover {{
            color: #38bdf8;
            background-color: #243347;
        }}
        th.sortable::after {{
            content: ' ↕';
            font-size: 0.8em;
            opacity: 0.4;
        }}
        th.sort-asc::after {{ content: ' ↑'; opacity: 1; color: #38bdf8; }}
        th.sort-desc::after {{ content: ' ↓'; opacity: 1; color: #38bdf8; }}

        tr {{ border-bottom: 1px solid #334155; }}
        tr:hover {{ background-color: #273549; }}
        td {{ padding: 12px 14px; text-align: center; }}
        
        .number {{ font-variant-numeric: tabular-nums; font-weight: 500; }}
        
        .pos-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            color: white;
            display: inline-block;
            width: 45px;
            text-align: center;
        }}
        .pos-tw {{ background-color: #eab308; color: #000; }}
        .pos-abw {{ background-color: #2563eb; }}
        .pos-mf {{ background-color: #16a34a; }}
        .pos-st {{ background-color: #dc2626; }}

        .player-name-container {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .player-name-text {{
            max-width: 220px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        /* UNIFORME KREIS-KLASSE FÜR ALLE INDIKATOREN */
        .indicator-circle {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            line-height: 1;
            flex-shrink: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.25);
        }}

        /* Medizinischer Status */
        .status-fit {{ background-color: #15803d; }}
        .status-injured {{ background-color: #b45309; }}
        .status-training {{ background-color: #1d4ed8; }}
        .status-suspended {{ background-color: #7f1d1d; }}
        .status-away {{ background-color: #4b5563; }}
        .status-out {{ background-color: #991b1b; }}
        .status-alert {{ background-color: #6b21a8; }}

        /* Aufstellungswahrscheinlichkeit */
        .prob-safe {{ background-color: #1e3a8a; }}
        .prob-high {{ background-color: #16a34a; }}
        .prob-medium {{ background-color: #c2410c; }}
        .prob-low {{ background-color: #991b1b; }}
        .prob-none {{ background-color: #1e293b; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Spielerliste</h1>
                <div class="stand">Stand: {aktuelles_datum}</div>
            </div>
            <div style="display: flex; gap: 10px;">
                <a href="index.html" class="nav-link">Dashboard</a>
                <a href="kader.html" class="nav-link">Kader</a>
            </div>
        </header>

        <div class="card">
            <div class="filter-container">
                <input type="text" id="playerSearch" class="search-input" onkeyup="filterTable()" placeholder="Nach Name oder Team suchen...">
                
                <!-- 1. FILTER: TEAMS (Hinterlegung ist aktiv) -->
                <div class="dropdown">
                    <button type="button" class="dropdown-button" id="teamDropdownBtn" onclick="toggleDropdown(event, 'teamDropdownOptions')">
                        <span>Teams filtern</span> <span>▼</span>
                    </button>
                    <div class="dropdown-content" id="teamDropdownOptions">
                        {dropdown_options_html}
                    </div>
                </div>

                <!-- 2. FILTER: POSITIONEN -->
                <div class="dropdown">
                    <button type="button" class="dropdown-button" id="posDropdownBtn" onclick="toggleDropdown(event, 'posDropdownOptions')">
                        <span>Positionen</span> <span>▼</span>
                    </button>
                    <div class="dropdown-content" id="posDropdownOptions">
                        <label class="dropdown-item"><input type="checkbox" value="TW" onchange="filterTable()"> Torwart (TW)</label>
                        <label class="dropdown-item"><input type="checkbox" value="ABW" onchange="filterTable()"> Abwehr (ABW)</label>
                        <label class="dropdown-item"><input type="checkbox" value="MF" onchange="filterTable()"> Mittelfeld (MF)</label>
                        <label class="dropdown-item"><input type="checkbox" value="ANG" onchange="filterTable()"> Sturm (ANG)</label>
                    </div>
                </div>

                <!-- 3. FILTER: WAHRSCHEINLICHKEIT -->
                <div class="dropdown">
                    <button type="button" class="dropdown-button" id="probDropdownBtn" onclick="toggleDropdown(event, 'probDropdownOptions')">
                        <span>Sterne filtern</span> <span>▼</span>
                    </button>
                    <div class="dropdown-content" id="probDropdownOptions">
                        <label class="dropdown-item"><input type="checkbox" value="1" onchange="filterTable()"> ⭐ Sicher Startelf</label>
                        <label class="dropdown-item"><input type="checkbox" value="2" onchange="filterTable()"> ✔️ Sehr wahrscheinlich</label>
                        <label class="dropdown-item"><input type="checkbox" value="3" onchange="filterTable()"> ❓ Möglich / Rotation</label>
                        <label class="dropdown-item"><input type="checkbox" value="4" onchange="filterTable()"> ⚠️ Unwahrscheinlich</label>
                        <label class="dropdown-item"><input type="checkbox" value="5" onchange="filterTable()"> ✖️ Keine Startelf / Ausfall</label>
                    </div>
                </div>

                <!-- 4. FILTER: STATUS -->
                <div class="dropdown">
                    <button type="button" class="dropdown-button" id="statusDropdownBtn" onclick="toggleDropdown(event, 'statusDropdownOptions')">
                        <span>Status filtern</span> <span>▼</span>
                    </button>
                    <div class="dropdown-content" id="statusDropdownOptions">
                        <label class="dropdown-item"><input type="checkbox" value="0" onchange="filterTable()"> ✔️ Fit</label>
                        <label class="dropdown-item"><input type="checkbox" value="2" onchange="filterTable()"> 🩹 Angeschlagen</label>
                        <label class="dropdown-item"><input type="checkbox" value="4" onchange="filterTable()"> 🏋️ Aufbautraining</label>
                        <label class="dropdown-item"><input type="checkbox" value="1" onchange="filterTable()"> ❌ Verletzt / Ausfall</label>
                        <label class="dropdown-item"><input type="checkbox" value="256" onchange="filterTable()"> ⏳ Abwesend</label>
                        <label class="dropdown-item"><input type="checkbox" value="8" onchange="filterTable()"> 🟥 Gesperrt</label>
                    </div>
                </div>
            </div>

            <table id="playerTable">
                <thead>
                    <tr>
                        <th style="text-align: left;">Spieler</th>
                        <th>Pos</th>
                        <th style="text-align: left;">Team</th>
                        <th class="sortable number" id="th-ap" onclick="sortTable(3, 'num')">Durchschnittspunkte</th>
                        <th class="sortable number sort-desc" id="th-mv" onclick="sortTable(4, 'num')">Marktwert</th>
                        <th>Besitzer</th>
                    </tr>
                </thead>
                <tbody>
                    {player_rows_html}
                </tbody>
            </table>
        </div>
    </div>

    <script>
    function toggleDropdown(e, id) {{
        e.stopPropagation();
        document.querySelectorAll('.dropdown-content').forEach(el => {{
            if(el.id !== id) el.classList.remove('show');
        }});
        document.getElementById(id).classList.toggle("show");
    }}

    document.addEventListener("click", function() {{
        document.querySelectorAll('.dropdown-content').forEach(el => el.classList.remove("show"));
    }});
    
    document.querySelectorAll('.dropdown-content').forEach(el => {{
        el.addEventListener("click", function(e) {{
            e.stopPropagation();
        }});
    }});

    function filterTable() {{
        const searchInput = document.getElementById("playerSearch").value.toLowerCase();
        
        const teamCheckboxes = document.querySelectorAll("#teamDropdownOptions input[type='checkbox']");
        let selectedTeams = [];
        teamCheckboxes.forEach(cb => {{ if (cb.checked) selectedTeams.push(cb.value.toLowerCase()); }});

        const posCheckboxes = document.querySelectorAll("#posDropdownOptions input[type='checkbox']");
        let selectedPositions = [];
        posCheckboxes.forEach(cb => {{ if (cb.checked) selectedPositions.push(cb.value.toUpperCase()); }});

        const probCheckboxes = document.querySelectorAll("#probDropdownOptions input[type='checkbox']");
        let selectedProbs = [];
        probCheckboxes.forEach(cb => {{ if (cb.checked) selectedProbs.push(cb.value); }});

        const statusCheckboxes = document.querySelectorAll("#statusDropdownOptions input[type='checkbox']");
        let selectedStati = [];
        statusCheckboxes.forEach(cb => {{ if (cb.checked) selectedStati.push(cb.value); }});

        document.getElementById("teamDropdownBtn").querySelector("span").textContent = selectedTeams.length === 0 ? "Teams filtern" : "Teams (" + selectedTeams.length + ")";
        document.getElementById("posDropdownBtn").querySelector("span").textContent = selectedPositions.length === 0 ? "Positionen" : "Pos (" + selectedPositions.length + ")";
        document.getElementById("probDropdownBtn").querySelector("span").textContent = selectedProbs.length === 0 ? "Sterne filtern" : "Sterne (" + selectedProbs.length + ")";
        document.getElementById("statusDropdownBtn").querySelector("span").textContent = selectedStati.length === 0 ? "Status filtern" : "Status (" + selectedStati.length + ")";

        const rows = document.getElementById("playerTable").getElementsByTagName("tbody")[0].getElementsByTagName("tr");
        for (let row of rows) {{
            if (row.cells.length < 3) continue;

            const playerName = row.cells[0].textContent.toLowerCase();
            const playerPos = row.cells[1].getAttribute('data-pos').toUpperCase();
            const teamName = row.cells[2].textContent.toLowerCase();
            const playerProb = row.getAttribute('data-prob');
            const playerStatus = row.getAttribute('data-status');

            const matchesSearch = playerName.includes(searchInput) || teamName.includes(searchInput);
            const matchesTeam = selectedTeams.length === 0 || selectedTeams.includes(teamName);
            const matchesPos = selectedPositions.length === 0 || selectedPositions.includes(playerPos);
            const matchesProb = selectedProbs.length === 0 || selectedProbs.includes(playerProb);
            const matchesStatus = selectedStati.length === 0 || selectedStati.includes(playerStatus);

            if (matchesSearch && matchesTeam && matchesPos && matchesProb && matchesStatus) {{
                row.style.display = "";
            }} else {{
                row.style.display = "none";
            }}
        }}
    }}

    let currentSortCol = 4;
    let isAsc = false;

    function sortTable(colIndex, type) {{
        const table = document.getElementById("playerTable");
        const tbody = table.tBodies[0];
        const rows = Array.from(tbody.rows);
        
        if (rows.length === 1 && rows[0].cells.length < 3) return;

        const thAP = document.getElementById("th-ap");
        const thMV = document.getElementById("th-mv");

        if (currentSortCol === colIndex) {{
            isAsc = !isAsc;
        }} else {{
            isAsc = false;
            currentSortCol = colIndex;
        }}

        thAP.classList.remove("sort-asc", "sort-desc");
        thMV.classList.remove("sort-asc", "sort-desc");
        
        const activeTh = colIndex === 3 ? thAP : thMV;
        activeTh.classList.add(isAsc ? "sort-asc" : "sort-desc");

        const direction = isAsc ? 1 : -1;

        rows.sort((a, b) => {{
            let valA = parseFloat(a.cells[colIndex].getAttribute('data-val')) || 0;
            let valB = parseFloat(b.cells[colIndex].getAttribute('data-val')) || 0;
            return (valA - valB) * direction;
        }});

        rows.forEach(row => tbody.appendChild(row));
    }}
    </script>
</body>
</html>
"""

    with open("spielerliste.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("spielerliste.html erfolgreich generiert!")