import os
import requests
from dotenv import load_dotenv

# Lädt die .env Datei, falls sie lokal existiert (wird ignoriert, wenn online über GitHub Secrets gelaufen wird)
load_dotenv()

class KickbaseClient:
    BASE_URL = "https://api.kickbase.com/v4"

    def __init__(self):
        self.token = None

    def login(self):
        # Holt die Variablen aus der .env oder den GitHub Secrets
        email = os.environ.get("KB_USER")
        password = os.environ.get("KB_PASSWORD")

        if not email or not password:
            raise Exception("Fehler: KB_USER oder KB_PASSWORD Umgebungsvariable fehlt!")

        url = f"{self.BASE_URL}/user/login"
        payload = {
            "em": email,
            "loy": False,
            "pass": password,
            "rep": {}
        }
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        
        print("Starte Login...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        self.token = data.get("tkn")
        print("Login erfolgreich!")
        return data

    def _headers(self):
        if not self.token:
            raise Exception("Error: Du bist nicht eingeloggt. Token fehlt.")
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def get_request(self, url, params=None):
        """Hilfsfunktion für GET-Anfragen, um doppelten Code zu vermeiden."""
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        
        # Da deine anderen Funktionen (z.B. für Transfers) direkt mit dem JSON/Dict 
        # arbeiten, geben wir hier direkt response.json() statt des rohen Objekts zurück.
        return response.json()