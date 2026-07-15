import os
import requests

class KickbaseClient:
    BASE_URL = "https://api.kickbase.com/v4"

    def __init__(self):
        self.token = None

    def login(self):
        email = os.environ.get("KICKBASE_EMAIL")
        password = os.environ.get("KICKBASE_PASSWORD")

        if not email or not password:
            raise Exception("Fehler: KICKBASE_EMAIL oder KICKBASE_PASSWORD Umgebungsvariable fehlt!")

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
        return response
