import os
import json

def run_generate_html_dashboard():
    print("Starte: run_generate_html_dashboard...")
    
    # 1. Daten aus vorhandenen TXT-Dateien auslesen
    # Hier passen wir uns flexibel an das an, was deine anderen Skripte schreiben
    squad_values = []
    
    # Beispielhaftes Einlesen: Falls du eine Datei hast, die Manager-Werte speichert
    # Falls deine Datei anders heißt (z.B. "Kontostände.txt"), passe den Namen an
    tx_filename = "Transactionen.txt" 
    
    # Wir erstellen ein paar Dummy-Daten basierend auf deinen Managern, 
    # falls die echten Berechnungsdateien noch nicht ausgelesen wurden:
    managers = {
        "2446378": "CoachLeisi", "165539": "Braunbär7", "2218524": "Julian",
        "2216931": "Timo Kramer", "2202080": "Sascha187", "2558680": "Joel",
        "3183264": "MirkoHengst", "3180066": "Philipp", "2202088": "Robinho",
        "717710": "Vincent", "2219496": "Vanilleeis23"
    }
    
    # HINWEIS: Wenn du eine fertige Datei mit den Teamwerten hast (z.B. "squad_values.json" oder .txt),
    # kannst du sie hier einlesen. Übergangsweise bauen wir eine Liste aus deinen bekannten Managern:
    display_data = []
    for m_id, name in managers.items():
        # Hier kannst du später die echten berechneten Werte zuordnen
        # Für dieses Beispiel nehmen wir einen Platzhalter-Wert, den du mit deinen echten Variablen fütterst
        display_data.append({
            "name": name,
            "value": 100000000  # Hier kommt dein echter Teamwert hin
        })

    # Sortieren: Höchster Teamwert zuerst
    display_data.sort(key=lambda x: x.get('value', 0), reverse=True)

    # 2. Die letzten Transfers aus der "Transactionen.txt" lesen, um sie auf der Website anzuzeigen!
    transfer_rows_html = ""
    if os.path.exists("Transactionen.txt"):
        try:
            with open("Transactionen.txt", "r", encoding="utf-8") as f:
                # Die letzten 5 Transfers einlesen
                lines = [f.readline().strip() for _ in range(5)]
                for line in lines:
                    if not line:
                        continue
                    entry = json.loads(line)
                    
                    # Parsen wie im Konsolen-Print
                    manager, action, spieler, preis = "", "", "", 0
                    for item in entry:
                        if "byr" in item:
                            manager, action = item["byr"], "Kauf"
                        elif "slr" in item:
                            manager, action = item["slr"], "Verkauf"
                        elif "pn" in item:
                            spieler = item["pn"]
                        elif "trp" in item:
                            preis = item["trp"]
                    
                    preis_formatiert = f"{preis:,}".replace(",", ".") + " €"
                    badge_color = "#22c55e" if action == "Kauf" else "#ef4444"
                    
                    transfer_rows_html += f"""
                    <tr>
                        <td><span style="background-color: {badge_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;">{action}</span></td>
                        <td>{manager}</td>
                        <td>{spieler}</td>
                        <td style="text-align: right;">{preis_formatiert}</td>
                    </tr>
                    """
        except Exception as e:
            transfer_rows_html = f"<tr><td colspan='4'>Fehler beim Laden der Transfers: {e}</td></tr>"
    else:
        transfer_rows_html = "<tr><td colspan='4'>Noch keine Transfers aufgezeichnet.</td></tr>"

    # 3. Das HTML-Template zusammenbauen
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kickbase Liga Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; margin: 0; padding: 20px; color: #e2e8f0; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #fff; margin-bottom: 30px; font-size: 2.5em; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }}
        .grid {{ display: grid; grid-template-columns: 1fr; gap: 20px; }}
        @media(min-width: 768px) {{ .grid {{ grid-template-columns: 3fr 2fr; }} }}
        .card {{ background: #1e293b; padding: 24px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); border: 1px solid #334155; }}
        h2 {{ margin-top: 0; color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px 12px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 0.85em; }}
        tr:hover {{ background-color: #1e293b; }}
        .number {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 500; }}
        .rank {{ font-weight: bold; width: 40px; text-align: center; color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Kickbase Liga-Dashboard</h1>
        
        <div class="grid">
            <!-- Linke Spalte: Tabelle der Manager -->
            <div class="card">
                <h2>Tabelle</h2>
                <table>
                    <thead>
                        <tr>
                            <th class="rank">#</th>
                            <th>Manager</th>
                            <th class="number">Teamwert</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for rank, manager in enumerate(display_data, 1):
        name = manager.get('name')
        value = manager.get('value', 0)
        value_formated = f"{value:,}".replace(",", ".") + " €"
        
        html_content += f"""
                        <tr>
                            <td class="rank">{rank}</td>
                            <td><strong>{name}</strong></td>
                            <td class="number" style="color: #4ade80;">{value_formated}</td>
                        </tr>"""

    html_content += f"""
                    </tbody>
                </table>
            </div>

            <!-- Rechte Spalte: Letzte Aktivitäten / Transfers -->
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
        </div>
    </div>
</body>
</html>
"""

    # Datei schreiben
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("index.html erfolgreich im Hauptverzeichnis generiert!")