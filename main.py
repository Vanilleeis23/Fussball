from kickbase_client import KickbaseClient

# Importiere die ausgelagerten Task-Funktionen
from tasks.task_transfers import get_transfers, run_ueber_markt_gelaufen
from tasks.task_market_squad import run_squad_value, run_market_players
from tasks.task_finances import (
    run_calculate_kontostand,
    run_calculate_max_bid,
    run_real_kontostand,
    run_calculate_kapital
)
from tasks.task_html_dashboard import run_generate_html_dashboard

def main():
    # 1. API Client initialisieren & einloggen
    kb = KickbaseClient()
    kb.login()

    # 2. Daten abfragen & speichern
    get_transfers(kb)
    run_squad_value(kb)
    run_market_players(kb)
    
    # 3. Finanzen berechnen (Reihenfolge ist wichtig, da sie aufeinander aufbauen!)
    run_calculate_kontostand()
    run_calculate_max_bid()
    run_real_kontostand()
    run_calculate_kapital()

    # 4. Zusätzliche Analysen
    run_ueber_markt_gelaufen(kb)
    run_generate_html_dashboard()
    print("Alle Aufgaben erfolgreich ausgeführt!")

if __name__ == "__main__":
    main()
