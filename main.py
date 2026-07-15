from kickbase_client import KickbaseClient

def main():
    kb = KickbaseClient()
    login_response = kb.login()
    kb.get_transfers()
    kb.getSquadValue()
    kb.calculateKontostand()
    kb.calculateMaxBid()
    kb.getMarketPlayers()
    kb.getRealKontostand()
    kb.CalculateKapital()
    kb.UeberMarktGelaufen()
    kb.AblaufSpieler()


if __name__ == "__main__":
    main()
