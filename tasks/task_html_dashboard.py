import os
import json

def read_value_from_file(filename, manager_name, default_value=0):
    """
    Hilfsfunktion, um einen Wert für einen bestimmten Manager aus einer TXT-Datei zu lesen.
    Unterstützt Formate wie 'Managername: 123456' oder rohen Text.
    """
    if not os.path.exists(filename):
        return default_value
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if manager_name.lower() in line.lower():
                    parts = line.split(":")
                    if len(parts) > 1:
                        clean_val = parts[1].replace("€", "").replace(".", "").replace(",", "").strip()
                        return int(clean_val)
    except Exception as e:
        print(f"Fehler beim Lesen von {filename} für {manager_name}: {e}")
    return default_value

def run_generate_html_dashboard():
    print("Starte: run_generate_html_dashboard...")
    
    managers = {
        "2446378": "CoachLeisi", "165539": "Braunbär7", "2218524": "Julian",
        "2216931": "Timo Kramer", "2202080": "Sascha187", "2558680": "Joel",
        "3183264": "MirkoHengst", "3180066": "Philipp", "2202088": "Robinho",
        "717710": "Vincent", "2219496": "Vanilleeis23"
    }
    
    display_data = []
    
    for m_id, name in managers.items():
        team_wert = read_value_from_file("Teamwerte.txt", name, default_value=0)
        kontostand = read_value_from_file("Kontostaende.txt", name, default_value=0)
        realer_kontostand = read_value_from_file("RealKontostand.txt", name, default_value=0)
        max_bid = read_value_from_file("MaxBid.txt", name, default_value=0)
        kapital = read_value_from_file("Kapital.txt", name, default_value=0)
        
        markt_spieler = ["Keine"] 

        display_data.append({
            "name": name,
            "team_wert": team_wert,
            "kontostand": kontostand,
            "realer_kontostand": realer_kontostand,
            "kapital": kapital,
            "max_bid": max_bid,
            "markt_spieler": ", ".join(markt_spieler)
        })

    # Standard-Sortierung auf der Website: Höchster realer Kontostand zuerst
    display_data.sort(key=lambda x: x.get('realer_kontostand', 0), reverse=True)

    # -------------------------------------------------------------------------
    # 2. TRANSFAKTIVITÄTEN AUSLESEN (Rechte Spalte)
    # -------------------------------------------------------------------------
    transfer_rows_html = ""
    if os.path.exists("Transactionen.txt"):
        try:
            with open("Transactionen.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-5:]: # Die letzten 5 Transfers
                    line = line.strip()
                    if not line: continue
                    entry = json.loads(line)
                    manager, action, spieler, preis = "", "", "", 0
                    for item in entry:
                        if "byr" in item: manager, action = item["byr"], "Kauf"
                        elif "slr" in item: manager, action = item["slr"], "Verkauf"
                        elif "pn" in item: spieler = item["pn"]
                        elif "trp" in item: preis = item["trp"]
                    
                    preis_formatiert = f"{preis:,}".replace(",", ".") + " €"
                    badge_color = "#22c55e" if action == "Kauf" else "#ef4444"
                    
                    transfer_rows_html += f"""
                    <tr>
                        <td><span style="background-color: {badge_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;">{action}</span></td>
                        <td>{manager}</td>
                        <td>{spieler}</td>
                        <td style="text-align: right;">{preis_formatiert}</td>
                    </tr>"""
        except Exception as e:
            transfer_rows_html = f"<tr><td colspan='4'>Fehler beim Laden der Transfers: {e}</td></tr>"
    else:
        transfer_rows_html = "<tr><td colspan='4'>Noch keine Transfers aufgezeichnet.</td></tr>"

    # -------------------------------------------------------------------------
    # 3. SPIELER ÜBER MARKT GELAUFEN AUSLESEN (NEU, Rechte Spalte unten)
    # -------------------------------------------------------------------------
    markt_verlauf_rows_html = ""
    if os.path.exists("ÜberMarktGelaufen.txt"):
        try:
            with open("ÜberMarktGelaufen.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Zeigt die letzten 8 Einträge an, damit die Liste aktuell bleibt
                for line in lines[-8:]:
                    line = line.strip()
                    if not line: continue
                    
                    # Falls das Format z.B. "Spielername: Marktwert/Info" ist
                    if ":" in line:
                        parts = line.split(":", 1)
                        s_name = parts[0].strip()
                        s_info = parts[1].strip()
                        
                        # Versuche Zahlenwerte schön als Währung zu formatieren
                        try:
                            clean_info = s_info.replace("€", "").replace(".", "").replace(",", "").strip()
                            num_info = int(clean_info)
                            s_info = f"{num_info:,}".replace(",", ".") + " €"
                        except ValueError:
                            pass
                            
                        markt_verlauf_rows_html += f"""
                        <tr>
                            <td style="font-weight: 500; color: #fff;">{s_name}</td>
                            <td style="text-align: right; color: #94a3b8;">{s_info}</td>
                        </tr>"""
                    else:
                        # Einfache Zeile, falls kein Trennzeichen vorhanden ist
                        markt_verlauf_rows_html += f"""
                        <tr>
                            <td colspan="2" style="color: #e2e8f0;">{line}</td>
                        </tr>"""
        except Exception as e:
            markt_verlauf_rows_html = f"<tr><td colspan='2'>Fehler beim Lesen der Markt-Historie: {e}</td></tr>"
    else:
        markt_verlauf_rows_html = "<tr><td colspan='2'>Keine Einträge in ÜberMarktGelaufen.txt gefunden.</td></tr>"

    # -------------------------------------------------------------------------
    # 4. HTML & CSS GENERIEREN
    # -------------------------------------------------------------------------
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kickbase Liga Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; margin: 0; padding: 20px; color: #e2e8f0; }}
        .container {{ max-width: 1550px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #fff; margin-bottom: 30px; font-size: 2.5em; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }}
        .grid {{ display: grid; grid-template-columns: 1fr; gap: 20px; }}
        @media(min-width: 1024px) {{ .grid {{ grid-template-columns: 3.5fr 1.5fr; }} }}
        .card {{ background: #1e293b; padding: 24px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); border: 1px solid #334155; overflow-x: auto; margin-bottom: 20px; }}
        h2 {{ margin-top: 0; color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 0.95em; }}
        th {{ color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 0.8em; letter-spacing: 0.5px; cursor: pointer; user-select: none; }}
        th:hover {{ color: #38bdf8; background-color: #1e293b; }}
        th.sort-asc::after {{ content: " ▴"; }}
        th.sort-desc::after {{ content: " ▾"; }}
        tr:hover {{ background-color: #161e2e; }}
        .number {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 500; }}
        .manager-name {{ font-weight: bold; color: #fff; }}
        .players-list {{ font-size: 0.85em; color: #94a3b8; max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .players-list:hover {{ white-space: normal; overflow: visible; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Kickbase Liga-Dashboard</h1>
        
        <div class="grid">
            <!-- Linke Spalte: Haupttabelle -->
            <div class="card">
                <h2>Manager Übersicht <span style="font-size: 0.5em; color: #64748b;">(Klicke Spalten zum Sortieren)</span></h2>
                <table id="managerTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0, 'str')">Manager</th>
                            <th class="number" onclick="sortTable(1, 'num')">Teamwert</th>
                            <th class="number" onclick="sortTable(2, 'num')">Kontostand</th>
                            <th class="number" onclick="sortTable(3, 'num')">Realer Konto</th>
                            <th class="number" onclick="sortTable(4, 'num')">Kapital</th>
                            <th class="number" onclick="sortTable(5, 'num')">Max Bid</th>
                            <th>Spieler auf Markt</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for manager in display_data:
        tw = f"{manager['team_wert']:,}".replace(",", ".")
        ks = f"{manager['kontostand']:,}".replace(",", ".")
        rk = f"{manager['realer_kontostand']:,}".replace(",", ".")
        kap = f"{manager['kapital']:,}".replace(",", ".")
        mb = f"{manager['max_bid']:,}".replace(",", ".")

        html_content += f"""
                        <tr>
                            <td class="manager-name">{manager['name']}</td>
                            <td class="number" data-val="{manager['team_wert']}" style="color: #4ade80;">{tw} €</td>
                            <td class="number" data-val="{manager['kontostand']}" style="color: #38bdf8;">{ks} €</td>
                            <td class="number" data-val="{manager['realer_kontostand']}" style="color: #fbbf24;">{rk} €</td>
                            <td class="number" data-val="{manager['kapital']}" style="color: #a78bfa;">{kap} €</td>
                            <td class="number" data-val="{manager['max_bid']}" style="color: #f87171;">{mb} €</td>
                            <td class="players-list" title="{manager['markt_spieler']}">{manager['markt_spieler']}</td>
                        </tr>"""

    html_content += f"""
                    </tbody>
                </table>
            </div>

            <!-- Rechte Spalte: Aktivitäten & Markt-Log -->
            <div>
                <div class="card">
                    <h2>Letzte Transfers</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Typ</th>
                                <th>Manager</th>
                                <th>Spieler</th>
                                <th style="text-align: right;">Betrag</th>
                            </tr>
                        </thead>
                        <tbody>
                            {transfer_rows_html}
                        </tbody>
                    </table>
                </div>

                <div class="card">
                    <h2>Zuletzt auf dem Markt</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Spieler</th>
                                <th style="text-align: right;">Info / Wert</th>
                            </tr>
                        </thead>
                        <tbody>
                            {markt_verlauf_rows_html}
                        </tbody>
                    </table>
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
        
    print("index.html erfolgreich inklusive Markt-Verlauf generiert!")