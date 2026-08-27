import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================================================================
# CONFIGURATION
# =========================================================================
LEAGUE_ID = "2556726"

MANAGER_IDS = {
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

def load_balances_from_txt(filename="Kontostand.txt"):
    """
    Liest die Kontostände aus einer Textdatei ein.
    Erwartet Zeilen wie: 'CoachLeisi: 15.230.500' oder 'Joel: -2.300.000'
    """
    balances = {}
    if not os.path.exists(filename):
        print(f"Hinweis: {filename} nicht gefunden. Alle Kontostände werden auf 0 gesetzt.")
        return balances

    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                
                parts = line.split(":", 1)
                name = parts[0].strip()
                val_str = parts[1].strip()
                
                val_str = val_str.replace(".", "").replace("€", "").strip()
                
                try:
                    balance_val = int(val_str)
                    balances[name] = balance_val
                except ValueError:
                    continue
        print(f"Kontostände erfolgreich aus {filename} geladen.")
    except Exception as e:
        print(f"Fehler beim Lesen der {filename}: {e}")
        
    return balances

def load_maxbids_from_txt(filename="maxbide.txt"):
    """
    Liest die MaxBids aus einer Textdatei ein.
    Erwartet Zeilen wie: 'CoachLeisi: 45.000.000'
    """
    maxbids = {}
    if not os.path.exists(filename):
        print(f"Hinweis: {filename} nicht gefunden. MaxBids werden dynamisch berechnet.")
        return maxbids

    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                
                parts = line.split(":", 1)
                name = parts[0].strip()
                val_str = parts[1].strip()
                
                val_str = val_str.replace(".", "").replace("€", "").strip()
                
                try:
                    maxbid_val = int(val_str)
                    maxbids[name] = maxbid_val
                except ValueError:
                    continue
        print(f"MaxBids erfolgreich aus {filename} geladen.")
    except Exception as e:
        print(f"Fehler beim Lesen der {filename}: {e}")
        
    return maxbids

def run_generate_squads_html(kb):
    """
    Generiert die kader.html unter Verwendung der Kontostand.txt und maxbide.txt.
    Spieler voll sichtbar (kein Scrollen), Manager-Karten ein-/ausklappbar.
    Inklusive interaktivem Verkaufs-Rechner für Kontostand, Realen Kaderwert, Reales MaxBid (33% Regel) und Spieleranzahl.
    """
    # 1. Kontostände & MaxBids aus lokalen Textdateien laden
    local_balances = load_balances_from_txt("Kontostand.txt")
    local_maxbids = load_maxbids_from_txt("maxbide.txt")

    squads_html_content = ""
    print(f"Starte Abfrage der Kader für Liga {LEAGUE_ID}...")

    for m_id, m_name in MANAGER_IDS.items():
        url = f"https://api.kickbase.com/v4/leagues/{LEAGUE_ID}/managers/{m_id}/squad"
        
        response = kb.get_request(url)
        if hasattr(response, "status_code"):
            if response.status_code == 200:
                squad_data = response.json()
            else:
                print(f"Fehler bei Manager {m_name}: {response.status_code}")
                continue
        else:
            squad_data = response

        if not squad_data:
            print(f"Keine Daten für {m_name} erhalten.")
            continue

        players = squad_data.get("it", [])
        
        # Sortierung: Höchster Marktwert zuerst
        players = sorted(players, key=lambda x: x.get("mv", 0), reverse=True)
        
        total_value = sum(p.get("mv", 0) for p in players)
        total_value_formatiert = f"{total_value:,}".replace(",", ".")
        player_count = len(players)
        
        manager_balance = local_balances.get(m_name, 0)
        balance_formatiert = f"{manager_balance:,}".replace(",", ".")
        balance_style = "color: #f87171;" if manager_balance < 0 else "color: #4ade80;"
        
        # MaxBid aus Datei oder alternativ berechnet (Kontostand + 33% des Kaderwerts)
        initial_calc_maxbid = manager_balance + int(total_value * 0.33)
        file_maxbid = local_maxbids.get(m_name, initial_calc_maxbid)
        file_maxbid_formatiert = f"{file_maxbid:,}".replace(",", ".")
        calc_maxbid_formatiert = f"{initial_calc_maxbid:,}".replace(",", ".")

        player_rows = ""
        for p in players:
            p_name = p.get("pn", "Unbekannter Spieler")
            p_mv = p.get("mv", 0)
            p_mv_formatiert = f"{p_mv:,}".replace(",", ".")
            
            p_prc = p.get("prc", 0)
            if p_prc is not None:
                p_prc_val = int(p_prc)
                p_prc_formatiert = f"{p_prc_val:,}".replace(",", ".")
            else:
                p_prc_val = 0
                p_prc_formatiert = "-"
            
            p_profit_val = p_mv - p_prc_val if p_prc_val > 0 else 0
            p_profit_formatiert = f"{p_profit_val:,}".replace(",", ".")
            
            if p_prc_val == 0:
                profit_style = "color: #94a3b8;"
                p_profit_formatiert = "-"
            elif p_profit_val > 0:
                profit_style = "color: #4ade80; font-weight: 500;"
                p_profit_formatiert = "+" + p_profit_formatiert
            elif p_profit_val < 0:
                profit_style = "color: #f87171; font-weight: 500;"
                p_profit_formatiert = p_profit_formatiert
            else:
                profit_style = "color: #f8fafc;"
            
            pos_mapping = {1: "TW", 2: "ABW", 3: "MF", 4: "ST"}
            pos_order = p.get("pos", 0)
            p_pos = pos_mapping.get(pos_order, "-")
            
            player_rows += f"""
            <tr>
                <td style="padding: 10px; text-align: center;" onclick="event.stopPropagation();">
                    <input type="checkbox" class="sale-checkbox" data-mv="{p_mv}" style="cursor: pointer; transform: scale(1.1);">
                </td>
                <td data-value="{p_name.lower()}" style="padding: 10px; text-align: left; font-weight: 500;">{p_name}</td>
                <td data-value="{pos_order}" style="padding: 10px; text-align: center;"><span class="pos-badge pos-{p_pos.lower()}">{p_pos}</span></td>
                <td data-value="{p_prc_val}" style="padding: 10px; text-align: right; font-variant-numeric: tabular-nums; color: #94a3b8;">{p_prc_formatiert}</td>
                <td data-value="{p_mv}" style="padding: 10px; text-align: right; font-variant-numeric: tabular-nums; font-weight: 500; color: #38bdf8;">{p_mv_formatiert}</td>
                <td data-value="{p_profit_val}" style="padding: 10px; text-align: right; font-variant-numeric: tabular-nums; {profit_style}">{p_profit_formatiert}</td>
            </tr>
            """
        
        if not player_rows:
            player_rows = "<tr><td colspan='6' style='text-align: center; color: #64748b; padding: 30px;'>Keine Spieler im Kader.</td></tr>"
        
        squads_html_content += f"""
        <div class="card active" data-base-balance="{manager_balance}" data-base-squad-value="{total_value}" data-base-count="{player_count}">
            <div class="card-header">
                <div class="title-area">
                    <span class="collapse-icon">▲</span>
                    <h3>{m_name}</h3>
                </div>
                <div class="meta-info" onclick="event.stopPropagation();">
                    <span>Spieler: <strong class="player-count">{player_count}</strong></span>
                    <span>Konto: <strong style="{balance_style}">{balance_formatiert} €</strong></span>
                    <span>Realer Kontostand: <strong class="real-balance" style="{balance_style}">{balance_formatiert} €</strong></span>
                    <span>Kaderwert: <strong>{total_value_formatiert} €</strong></span>
                    <span>Realer Kaderwert: <strong class="real-squad-value" style="color: #38bdf8;">{total_value_formatiert} €</strong></span>
                    <span>Maximalgebot: <strong>{file_maxbid_formatiert} €</strong></span>
                    <span>Reales Maximalgebot: <strong class="real-max-bid" style="color: #38bdf8;">{calc_maxbid_formatiert} €</strong></span>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: center; width: 40px;" onclick="event.stopPropagation();">Sel.</th>
                            <th class="sortable" style="text-align: left;">Spieler</th>
                            <th class="sortable" style="text-align: center;">Pos</th>
                            <th class="sortable" style="text-align: right;">Kaufpreis</th>
                            <th class="sortable class-mw sort-desc" style="text-align: right;">Marktwert</th>
                            <th class="sortable" style="text-align: right;">Profit</th>
                        </tr>
                    </thead>
                    <tbody>
                        {player_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    # =========================================================================
    # HTML GENERIERUNG mit JS Accordion, Sortierung & Live-Berechnung
    # =========================================================================
    tz_berlin = ZoneInfo("Europe/Berlin")
    aktuelles_datum = datetime.now(tz_berlin).strftime("%d.%m.%Y um %H:%M Uhr")
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Liga-Kader Übersicht</title>
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
            .nav-buttons {{
                display: flex;
                gap: 10px;
            }}
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
            .squads-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(550px, 1fr));
                gap: 25px;
                align-items: start;
            }}
            @media (max-width: 600px) {{
                .squads-grid {{ grid-template-columns: 1fr; }}
            }}
            .card {{
                background-color: #1e293b;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #334155;
                display: flex;
                flex-direction: column;
                transition: all 0.3s ease;
            }}
            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #334155;
                padding-bottom: 12px;
                cursor: pointer;
                user-select: none;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .card-header:hover {{
                background-color: #24334755;
            }}
            .title-area {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .collapse-icon {{
                font-size: 0.8em;
                color: #64748b;
                transition: transform 0.2s ease;
            }}
            .card-header h3 {{ margin: 0; font-size: 1.3em; color: #f1f5f9; }}
            .meta-info {{
                font-size: 0.85em;
                color: #94a3b8;
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
            }}
            .meta-info strong {{ color: #38bdf8; }}
            
            .table-container {{
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            
            .card.active .table-container {{
                max-height: 2000px;
            }}
            
            table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; margin-top: 10px; }}
            th {{
                background-color: #1e293b;
                color: #94a3b8;
                padding: 8px 10px;
                font-weight: 600;
                border-bottom: 2px solid #334155;
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
            tr.selected-for-sale {{ background-color: #1e3a8a33; }}
            
            .pos-badge {{
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 0.8em;
                font-weight: bold;
                color: white;
                display: inline-block;
                width: 32px;
                text-align: center;
            }}
            .pos-tw {{ background-color: #eab308; color: #000; }}
            .pos-abw {{ background-color: #2563eb; }}
            .pos-mf {{ background-color: #16a34a; }}
            .pos-st {{ background-color: #dc2626; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div>
                    <h1>Liga-Kader Übersicht</h1>
                    <div class="stand">Stand: {aktuelles_datum}</div>
                </div>
                <div class="nav-buttons">
                    <a href="index.html" class="nav-link">Dashboard</a>
                    <a href="spielerliste.html" class="nav-link">Spielerliste</a>
                </div>
            </header>
            
            <div class="squads-grid">
                {squads_html_content}
            </div>
        </div>

        <script>
        function formatEuro(val) {{
            return new Intl.NumberFormat('de-DE').format(val) + " €";
        }}

        // 1. COLLAPSIBLE ACCORDION FUNKTION
        document.querySelectorAll('.card-header').forEach(header => {{
            header.addEventListener('click', () => {{
                const card = header.closest('.card');
                const icon = card.querySelector('.collapse-icon');
                
                card.classList.toggle('active');
                
                if (card.classList.contains('active')) {{
                    icon.textContent = '▲';
                    icon.style.transform = 'rotate(0deg)';
                }} else {{
                    icon.textContent = '▼';
                    icon.style.transform = 'rotate(0deg)';
                }}
            }});
        }});

        // 2. LIVE-BERECHNUNG FÜR KONTOSTAND, REALEN KADERWERT, REALES MAXBID & SPIELERANZAHL
        document.querySelectorAll('.card').forEach(card => {{
            const baseBalance = parseInt(card.getAttribute('data-base-balance')) || 0;
            const baseSquadValue = parseInt(card.getAttribute('data-base-squad-value')) || 0;
            const baseCount = parseInt(card.getAttribute('data-base-count')) || 0;
            
            const realBalanceElem = card.querySelector('.real-balance');
            const realSquadValueElem = card.querySelector('.real-squad-value');
            const realMaxBidElem = card.querySelector('.real-max-bid');
            const playerCountElem = card.querySelector('.player-count');
            const checkboxes = card.querySelectorAll('.sale-checkbox');

            function updateCardStats() {{
                let extraCash = 0;
                let soldCount = 0;

                checkboxes.forEach(cb => {{
                    if (cb.checked) {{
                        extraCash += parseInt(cb.getAttribute('data-mv')) || 0;
                        soldCount++;
                        cb.closest('tr').classList.add('selected-for-sale');
                    }} else {{
                        cb.closest('tr').classList.remove('selected-for-sale');
                    }}
                }});

                // Dynamischer Kontostand
                const newBalance = baseBalance + extraCash;
                
                // Dynamischer Kaderwert
                const newSquadValue = Math.max(0, baseSquadValue - extraCash);
                
                // Maximales Minus (33% des verbleibenden Kaderwerts)
                const maxMinusAllowed = Math.floor(newSquadValue * 0.33);
                
                // Dynamisches MaxBid (Kontostand + maximales Minus)
                const newMaxBid = newBalance + maxMinusAllowed;

                realBalanceElem.textContent = formatEuro(newBalance);
                
                if (realSquadValueElem) {{
                    realSquadValueElem.textContent = formatEuro(newSquadValue);
                }}

                if (realMaxBidElem) {{
                    realMaxBidElem.textContent = formatEuro(newMaxBid);
                }}
                
                const newCount = baseCount - soldCount;
                playerCountElem.textContent = newCount;

                if (newBalance < 0) {{
                    realBalanceElem.style.color = '#f87171';
                }} else {{
                    realBalanceElem.style.color = '#4ade80';
                }}
            }}

            checkboxes.forEach(cb => {{
                cb.addEventListener('change', updateCardStats);
            }});
        }});

        // 3. INTERAKTIVE TABELLEN-SORTIERUNG
        document.querySelectorAll('th.sortable').forEach(headerCell => {{
            headerCell.addEventListener('click', () => {{
                const table = headerCell.closest('table');
                const thArray = Array.from(table.querySelectorAll('th'));
                const columnIndex = thArray.indexOf(headerCell);
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                const isAscending = headerCell.classList.contains('sort-asc');
                
                thArray.forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
                headerCell.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
                
                rows.sort((rowA, rowB) => {{
                    const cellA = rowA.children[columnIndex].getAttribute('data-value');
                    const cellB = rowB.children[columnIndex].getAttribute('data-value');
                    
                    const valA = isNaN(cellA) ? cellA : parseFloat(cellA);
                    const valB = isNaN(cellB) ? cellB : parseFloat(cellB);
                    
                    if (valA < valB) return isAscending ? 1 : -1;
                    if (valA > valB) return isAscending ? -1 : 1;
                    return 0;
                }});
                
                rows.forEach(row => tbody.appendChild(row));
            }});
        }});
        </script>
    </body>
    </html>
    """

    with open("kader.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("kader.html erfolgreich inklusive Realem Kaderwert generiert!")

if __name__ == "__main__":
    pass