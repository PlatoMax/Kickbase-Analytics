import requests
from dotenv import load_dotenv
import os
from scrape.config import API_URL, LEAGUE_NAME
from datetime import datetime, timezone
from scrape.scrape_stats import *

# eher allgemeinere Sachen während scrape_stats sich auf die Stats der Spieler fokussiert

load_dotenv()

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
    league_id = None
    for league in data["srvl"]:
        if league["name"] == LEAGUE_NAME:
            league_id = league["id"]
            break
        
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


def get_leaderboard(token, league_id, cookies):
    response = requests.get(
        f"{API_URL}/leagues/{league_id}/ranking",
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )

    if response.status_code != 200:
        print("Leaderboard-Abfrage failed")
        return []

    data = response.json()
    players = [(player["n"], player["sp"]) for player in data["us"]]
    return sorted(players, key=lambda x: x[1], reverse=True)

def get_season(last = False): # last = False -> aktuelle Saison, last = True -> letzte Saison
    current_year = datetime.now().year
    if datetime.now().month < 7:
        current_year -= 1

    if last:
        current_year -= 1

    return current_year


def get_kickbase_deadline(season):
    matches = get_data_matchdays(season)
    now = datetime.now(timezone.utc)

    all_matches = [
        (datetime.fromisoformat(m["matchDateTimeUTC"].replace("Z", "+00:00")), m["group"]["groupOrderID"]) 
        for m in matches
    ]

    future_matches = [m for m in all_matches if m[0] > now]
    
    if not future_matches:
        print("Keine zukünftigen Spiele gefunden.")
        return None

    upcoming_md = future_matches[0][1]

    md_already_started = any(m[1] == upcoming_md and m[0] < now for m in all_matches)

    target_md = upcoming_md + 1 if md_already_started else upcoming_md
    target_matches = [m[0] for m in all_matches if m[1] == target_md]
    
    if not target_matches:
        return None
        
    deadline_utc = min(target_matches)
    
    return {
        "matchday": target_md,
        "deadline_utc": deadline_utc
    }
        
