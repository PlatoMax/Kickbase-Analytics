import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_URL = "https://api.kickbase.com/v4"

def login():
    # Einloggen und Token + League-ID zurückgeben
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    response = requests.post(
        f"{API_URL}/user/login",
        json={"em": email, "pass": password, "loy": False, "rep": {}}
    )

    if response.status_code != 200:
        print("Login fehlgeschlagen!")
        return None, None, None

    data = response.json()
    token = data.get("tkn")
    league_id = data["srvl"][0]["id"]
    cookies = {"kkstrauth": response.cookies.get("kkstrauth")}

    return token, league_id, cookies


def get_market(token, league_id, cookies):
    # Spieler auf dem Transfermarkt abfragen
    response = requests.get(
        f"{API_URL}/leagues/{league_id}/market",
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )

    if response.status_code != 200:
        print("Markt-Abfrage fehlgeschlagen!")
        return []

    return response.json().get("it", [])


def get_squad(token, league_id, cookies):
    # Eigenes Team abfragen
    response = requests.get(
        f"{API_URL}/leagues/{league_id}/squad",
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )

    if response.status_code != 200:
        print("Squad-Abfrage fehlgeschlagen!")
        return []

    return response.json().get("it", [])


def get_budget(token, league_id, cookies):
    # Budget abfragen
    response = requests.get(
        f"{API_URL}/leagues/{league_id}/me/budget",
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )

    if response.status_code != 200:
        print("Budget-Abfrage fehlgeschlagen!")
        return {}

    return response.json()

