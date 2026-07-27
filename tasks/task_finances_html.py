import os
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def read_raw_line_from_file(filename, manager_name, default_value="0 €"):
    """
    Liest die komplette Zeile aus, splittet am Doppelpunkt und prüft,
    ob der gesuchte Managername im linken Teil enthalten ist.
    """
    if not os.path.exists(filename):
        print(f"Warnung: Datei {filename} wurde nicht gefunden.")
        return default_value
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    parts = line.split(":", 1)
                    name_part = parts[0].strip().lower()
                    value_part = parts[1].strip()
                    
                    if manager_name.lower() in name_part:
                        return value_part
    except Exception as e:
        print(f"Fehler beim Lesen von {filename} für {manager_name}: {e}")
    return default_value

def read_numeric_value_from_file(filename, manager_name, default_value=0):
    """
    Sucht den Managernamen im linken Teil des Doppelpunkts und
    extrahiert alle Ziffern aus dem rechten Teil.
    """
    if not os.path.exists(filename):
        print(f"Warnung: Datei {filename} wurde nicht gefunden.")
        return default_value
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    parts = line.split(":", 1)
                    name_part = parts[0].strip().lower()
                    value_part = parts[1].strip()
                    
                    if manager_name.lower() in name_part:
                        clean_chars = [c for c in value_part if c.isdigit() or c == '-']
                        clean_val = "".join(clean_chars)
                        if clean_val:
                            return int(clean_val)
    except Exception as e:
        print(f"Fehler beim numerischen Lesen von {filename} für {manager_name}: {e}")
    return default_value

def extract_first_number_from_string(text_str):
    """
    Isoliert die allererste Zahl vor der Klammer für die Sortierung des Realen Kontostands.
    """
    main_part = text_str.split("(")[0]
    clean_chars = [c for c in main_part if c.isdigit() or c == '-']
    clean_val = "".join(clean_chars)
    if clean_val:
        return int(clean_val)
    return 0

def format_realer_kontostand(text_str):
    """
    Formatiert den Text '65.439.984 € (Kontostand: 61.000.000 €, Spieler auf dem Markt: 4.439.984 €)'
    um in HTML-Zeilenumbrüche.
    """
    match = re.search(r"([\d.]+)\s*€\s*\((Kontostand:\s*[\d.]+)\s*€,\s*Spieler auf dem Markt:\s*([\d.]+)\s*€\)", text_str)
    if match:
        gesamt = match.group(1)
        konto = match.group(2)
        markt_wert = match.group(3)
        return f"{gesamt}<br>{konto}<br>Marktspieler: {markt_wert}"
    return text_str

def get_players_on_market_for_manager(filename, manager_name):
    """
    Liest die Datei mit der Pipe-Struktur (Spieler | Wert | Manager) aus
    und gibt eine Liste formatierter Strings zurück.
    """
    found_players = []
    if not os.path.exists(filename):
        return ["Keine"]
        
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "|" not in line:
                    continue
                
                parts = line.split("|")
                if len(parts) >= 3:
                    spieler = parts[0].strip()
                    wert = parts[1].strip()
                    m_name = parts[2].strip()
                    
                    if manager_name.lower() == m_name.lower():
                        wert_clean = wert.replace("€", "").replace(",", ".").strip()
                        found_players.append(f"{spieler} ({wert_clean})")
    except Exception as e:
        print(f"Fehler beim Lesen der Marktspieler-Datei: {e}")
        
    return found_players if found_players else ["Keine"]

def run_generate_html_dashboard():
    print("Starte: run_generate_html_dashboard...")
    
    managers = {
        "2446378": "CoachLeisi", "165539": "Braunbär7", "2218524": "Julian",
        "2216931": "Timo Kramer", "2202080": "Sascha187", "2558680": "Joel",
        "3183264": "MirkoHengst", "3180066": "Philipp", "2202088": "404",
        "717710": "Vincent", "2219496": "Vanilleeis23"
    }
    
    display_data = []
    
    for m_id, name in managers.items():
        team_wert = read_numeric_value_from_file("Kaderwert.txt", name, default_value=0)
        max_bid = read_numeric_value_from_file("MaxBide.txt", name, default_value=0)
        kapital = read_numeric_value_from_file("Kapital.txt", name, default_value=0)
        
        realer_kontostand_raw = read_raw_line_from_file("RealKontostand.txt", name, default_value="0 €")
        realer_kontostand_num = extract_first_number_from_string(realer_kontostand_raw)
        realer_kontostand_html = format_realer_kontostand(realer_kontostand_raw)
        
        markt_spieler = get_players_on_market_for_manager("MarketPlayer.txt", name)
  
        display_data.append({
            "name": name,
            "team_wert": team_wert,
            "realer_kontostand_html": realer_kontostand_html,
            "realer_kontostand_num": realer_kontostand_num,
            "kapital": kapital,
            "max_bid": max_bid,
            "markt_spieler": markt_spieler
        })

    display_data.sort(key=lambda x: x.get('realer_kontostand_num', 0), reverse=True)

    # -------------------------------------------------------------------------
    # 2. TRANSFAKTIVITÄTEN AUSLESEN (Rechte Spalte)
    # -------------------------------------------------------------------------
    transfer_rows_html = ""
    if os.path.exists("Transactionen.txt"):
        try:
            with open("Transactionen.txt", "r", encoding="utf-8") as f:
                lines = reversed(f.readlines())
                
                for line in lines:
                    line = line.strip()
                    if not line: 
                        continue
                    
                    entry = json.loads(line)
                    manager, action, spieler, preis, raw_datum = "", "", "", 0, ""
                    
                    for item in entry:
                        if isinstance(item, list) and len(item) == 2:
                            key, value = item[0], item[1]
                            if key == "byr": 
                                manager, action = value, "Kauf"
                            elif key == "slr": 
                                manager, action = value, "Verkauf"
                            elif key == "pn": 
                                spieler = value
                            elif key == "trp": 
                                preis = value
                            elif key in ["dt", "date", "time"]: 
                                raw_datum = str(value)
                        elif isinstance(item, dict):
                            if "byr" in item:
                                manager, action = item["byr"], "Kauf"
                            elif "slr" in item:
                                manager, action = item["slr"], "Verkauf"
                            if "pn" in item:
                                spieler = item["pn"]
                            if "trp" in item:
                                preis = item["trp"]
                            for d_key in ["dt", "date", "time"]:
                                if d_key in item:
                                    raw_datum = str(item[d_key])

                    datum_formatiert = "-"
                    if raw_datum:
                        try:
                            if "T" in raw_datum:
                                clean_dt = raw_datum.split(".")[0].split("+")[0].replace("Z", "")
                                dt_obj = datetime.strptime(clean_dt, "%Y-%m-%dT%H:%M:%S")
                            else:
                                dt_obj = datetime.fromisoformat(raw_datum)
                            
                            datum_formatiert = dt_obj.strftime("%d.%m.%Y<br>%H:%M")
                        except Exception:
                            datum_formatiert = raw_datum

                    if manager or spieler:
                        preis_formatiert = f"{preis:,}".replace(",", ".")
                        badge_color = "#22c55e" if action == "Kauf" else "#ef4444"
                        
                        transfer_rows_html += f"""
                        <tr>
                            <td style="text-align: center;"><span style="background-color: {badge_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;">{action}</span></td>
                            <td style="text-align: center;">{manager}</td>
                            <td style="text-align: center;">{spieler}</td>
                            <td style="text-align: center;">{preis_formatiert}</td>
                            <td style="text-align: center; color: #94a3b8; font-size: 0.85em; line-height: 1.2;">{datum_formatiert}</td>
                        </tr>"""
        except Exception as e:
            transfer_rows_html = f"<tr><td colspan='5' style='text-align: center;'>Fehler beim Laden der Transfers: {e}</td></tr>"
    else:
        transfer_rows_html = "<tr><td colspan='5' style='text-align: center;'>Noch keine Transfers aufgezeichnet.</td></tr>"

    # -------------------------------------------------------------------------
    # 3. SPIELER ÜBER MARKT GELAUFEN AUSLESEN (Rechte Spalte unten)
    # -------------------------------------------------------------------------
    markt_verlauf_rows_html = ""
    if os.path.exists("ÜberMarktGelaufen.txt"):
        try:
            with open("ÜberMarktGelaufen.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    line = line.strip()
                    if not line: continue
                    
                    if ":" in line:
                        parts = line.split(":", 1)
                        s_name = parts[0].strip()
                        s_info = parts[1].strip()
                        
                        try:
                            clean_info = s_info.replace("€", "").replace(".", "").replace(",", "").strip()
                            num_info = int(clean_info)
                            s_info = f"{num_info:,}".replace(",", ".") + " €"
                        except ValueError:
                            pass
                            
                        markt_verlauf_rows_html += f"""
                        <tr>
                            <td style="font-weight: 500; color: #fff; text-align: center;">{s_name}</td>
                            <td style="text-align: center; color: #94a3b8;">{s_info}</td>
                        </tr>"""
                    else:
                        markt_verlauf_rows_html += f"""
                        <tr>
                            <td colspan="2" style="color: #e2e8f0; text-align: center;">{line}</td>
                        </tr>"""
        except Exception as e:
            markt_verlauf_rows_html = f"<tr><td colspan='2' style='text-align: center;'>Fehler beim Lesen der Markt-Historie: {e}</td></tr>"

    # -------------------------------------------------------------------------
    # 4. ABLAUFDATUM AUSLESEN (Rechte Spalte ganz unten)
    # -------------------------------------------------------------------------
    ablauf_rows_html = ""
    if os.path.exists("Ablaufdatum.txt"):
        try:
            with open("Ablaufdatum.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    if ":" in line:
                        parts = line.split(":", 1)
                        spieler_name = parts[0].strip()
                        zeit_info = parts[1].strip()
                        ablauf_rows_html += f"""
                        <tr>
                            <td style="font-weight: 500; color: #fff; text-align: center;">{spieler_name}</td>
                            <td style="text-align: center; color: #f87171;">{zeit_info}</td>
                        </tr>"""
                    else:
                        ablauf_rows_html += f"""
                        <tr>
                            <td colspan="2" style="color: #e2e8f0; text-align: center;">{line}</td>
                        </tr>"""
        except Exception as e:
            ablauf_rows_html = f"<tr><td colspan='2' style='text-align: center;'>Fehler beim Lesen der Ablaufdaten: {e}</td></tr>"
    else:
        ablauf_rows_html = "<tr><td colspan='2' style='text-align: center;'>Keine Ablaufdaten gefunden.</td></tr>"

    # -------------------------------------------------------------------------
    # 5. HTML & CSS GENERIEREN
    # -------------------------------------------------------------------------
    tz_berlin = ZoneInfo("Europe/Berlin")
    aktuelles_datum = datetime.now(tz_berlin).strftime("%d.%m.%Y um %H:%M Uhr")

    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fußball</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; margin: 0; padding: 20px; color: #e2e8f0; }}
        .container {{ max-width: 1650px; margin: 0 auto; }}
        
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
        h1 {{ margin: 0; color: #38bdf8; font-size: 2.2em; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
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
        }}
        .nav-link:hover {{
            background-color: #38bdf8;
            color: #0f172a;
        }}

        .grid {{ display: grid; grid-template-columns: 1fr; gap: 20px; }}
        @media(min-width: 1280px) {{ .grid {{ grid-template-columns: 3.4fr 1.6fr; }} }}
        .card {{ background: #1e293b; padding: 24px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); border: 1px solid #334155; overflow-x: auto; margin-bottom: 20px; }}
        h2 {{ margin-top: 0; color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 10px; margin-bottom: 10px; }}
        
        .table-scroll-container {{
            max-height: 245px;
            overflow-y: auto;
            border-radius: 4px;
        }}
        
        .table-scroll-container::-webkit-scrollbar, .players-list::-webkit-scrollbar {{ width: 6px; }}
        .table-scroll-container::-webkit-scrollbar-track, .players-list::-webkit-scrollbar-track {{ background: #1e293b; }}
        .table-scroll-container::-webkit-scrollbar-thumb, .players-list::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 3px; }}
        .table-scroll-container::-webkit-scrollbar-thumb:hover, .players-list::-webkit-scrollbar-thumb:hover {{ background: #64748b; }}

        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 12px; text-align: center; border-bottom: 1px solid #334155; font-size: 0.95em; }}
        
        th {{ 
            color: #94a3b8; 
            font-weight: 600; 
            text-transform: uppercase; 
            font-size: 0.8em; 
            letter-spacing: 0.5px; 
            cursor: pointer; 
            user-select: none;
            position: sticky;
            top: 0;
            background-color: #1e293b;
            z-index: 10;
        }}
        th:hover {{ color: #38bdf8; }}
        th.sort-asc::after {{ content: " ▴"; }}
        th.sort-desc::after {{ content: " ▾"; }}
        tr:hover {{ background-color: #161e2e; }}
        .number {{ text-align: center; font-variant-numeric: tabular-nums; font-weight: 500; }}
        .real-kontostand-cell {{ font-variant-numeric: tabular-nums; font-weight: 500; text-align: center; line-height: 1.4; }}
        .manager-name {{ font-weight: bold; color: #fff; text-align: center; }}
        
        .players-list {{ 
            font-size: 0.85em; 
            color: #94a3b8; 
            max-height: 90px;      
            overflow-y: auto;      
            display: block;        
            text-align: center; 
            line-height: 1.4;
            min-width: 180px;
        }}
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
                        <a href="kader.html" class="nav-link">Kader</a>
                        <a href="playerlist.html" class="nav-link">Spielerliste</a>
                </div>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>Manager Übersicht <span style="font-size: 0.5em; color: #64748b;">(Klicke Spalten zum Sortieren)</span></h2>
                <table id="managerTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0, 'str')">Manager</th>
                            <th class="number" onclick="sortTable(1, 'num')">Teamwert</th>
                            <th onclick="sortTable(2, 'num')">Kontostand</th>
                            <th class="number" onclick="sortTable(3, 'num')">Kapital</th>
                            <th class="number" onclick="sortTable(4, 'num')">Maximalgebot</th>
                            <th>Spieler auf Markt</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for manager in display_data:
        tw = f"{manager.get('team_wert', 0):,}".replace(",", ".")
        kap = f"{manager.get('kapital', 0):,}".replace(",", ".")
        mb = f"{manager.get('max_bid', 0):,}".replace(",", ".")
        
        spieler_html = "<br>".join(manager.get('markt_spieler', []))
        spieler_title = ", ".join(manager.get('markt_spieler', []))

        html_content += f"""
                        <tr>
                            <td class="manager-name">{manager.get('name')}</td>
                            <td class="number" data-val="{manager.get('team_wert', 0)}" style="color: #4ade80;">{tw}</td>
                            <td class="real-kontostand-cell" data-val="{manager.get('realer_kontostand_num', 0)}" style="color: #fbbf24;">{manager.get('realer_kontostand_html')}</td>
                            <td class="number" data-val="{manager.get('kapital', 0)}" style="color: #a78bfa;">{kap}</td>
                            <td class="number" data-val="{manager.get('max_bid', 0)}" style="color: #f87171;">{mb}</td>
                            <td>
                                <span class="players-list" title="{spieler_title}">
                                    {spieler_html}
                                </span>
                            </td>
                        </tr>"""

    html_content += f"""
                    </tbody>
                </table>
            </div>

            <div>
                <div class="card" style="width: 100%; box-sizing: border-box;">
                    <h2>Letzte Transfers</h2>
                    <div class="table-scroll-container" style="max-height: 340px; overflow-y: auto; overflow-x: hidden; width: 100%;">
                        <table style="width: 100%; table-layout: fixed; border-collapse: collapse;">
                            <thead>
                                <tr>
                                    <th style="width: 15%; text-align: center; padding: 8px 4px;">Typ</th>
                                    <th style="width: 25%; text-align: center; padding: 8px 4px;">Manager</th>
                                    <th style="width: 20%; text-align: center; padding: 8px 4px;">Spieler</th>
                                    <th style="width: 20%; text-align: center; padding: 8px 4px;">Betrag</th>
                                    <th style="width: 20%; text-align: center; padding: 8px 4px;">Datum</th>
                                </tr>
                            </thead>
                            <tbody>
                                {transfer_rows_html}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="card">
                    <h2>Zuletzt auf dem Markt</h2>
                    <div class="table-scroll-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Spieler</th>
                                    <th>Info / Wert</th>
                                </tr>
                            </thead>
                            <tbody>
                                {markt_verlauf_rows_html}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="card">
                    <h2>Spieler Ablaufdatum</h2>
                    <div class="table-scroll-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Spieler</th>
                                    <th>Endet in</th>
                                </tr>
                            </thead>
                            <tbody>
                                {ablauf_rows_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    function sortTable(colIndex, type) {{
        const table = document.getElementById("managerTable");
        const tbody = table.tBodies[0];
        const rows = Array.from(tbody.rows);
        const th = table.querySelectorAll("thead th")[colIndex];
        const isAsc = th.classList.contains("sort-asc");
        
        table.querySelectorAll("thead th").forEach(h => h.classList.remove("sort-asc", "sort-desc"));
        th.classList.add(isAsc ? "sort-desc" : "sort-asc");
        const direction = isAsc ? -1 : 1;

        rows.sort((a, b) => {{
            let valA, valB;
            if (type === 'num') {{
                valA = parseFloat(a.cells[colIndex].getAttribute('data-val')) || 0;
                valB = parseFloat(b.cells[colIndex].getAttribute('data-val')) || 0;
            }} else {{
                valA = a.cells[colIndex].textContent.toLowerCase().trim();
                valB = b.cells[colIndex].textContent.toLowerCase().trim();
            }}
            if (valA < valB) return -1 * direction;
            if (valA > valB) return 1 * direction;
            return 0;
        }});
        rows.forEach(row => tbody.appendChild(row));
    }}
    </script>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("index.html erfolgreich generiert. Marktspieler werden nun dynamisch zugeordnet!")

if __name__ == "__main__":
    run_generate_html_dashboard()