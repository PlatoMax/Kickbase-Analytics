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

def get_squad(league_id, token, cookies):
    url = f"{API_URL}/leagues/{league_id}/squad"
    response = requests.get(url, headers={"tkn": token, "Accept": "application/json"}, cookies=cookies)

    try:
        data = response.json()
    except Exception as e:
        print(f"No response from get_squad: {e}")
        return None
    
    # print(data)    # Debug Ausgabe

    squad = []
    for player in data.get("it"):
        name = player.get("n")
        player_id = player.get("i")
        player_pos = int(player.get("pos"))
        team_id = player.get("tid")
        player_price = player.get("mv")

        squad.append({
            "Playername": name,
            "player_id": player_id,
            "player_pos": player_pos,
            "team_id": team_id,
            "player_price": player_price
        }
        )

    return squad

def get_budget(league_id, token, cookies):
    """Gets the user's budget for a given league_id."""

    url = f"{API_URL}/leagues/{league_id}/me/budget"
    response = requests.get(url, headers={"tkn": token, "Accept": "application/json"}, cookies=cookies)
    try: 
        data = response.json()
        return int(data.get("b", 0))
    except Exception as e:
        print(f"Fehler in get_budget: {e}")
        return 0



def get_leaderboard(league_id, token, cookies):
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


def get_kickbase_deadline(season, skip_started_matchday=True):
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

    if skip_started_matchday and md_already_started:
        upcoming_md += 1
    else:
        target_md = upcoming_md

    target_matches = [m[0] for m in all_matches if m[1] == target_md]
    
    if not target_matches:
        return None
        
    deadline_utc = min(target_matches)
    
    return {
        "matchday": target_md,
        "deadline_utc": deadline_utc
    }
        
