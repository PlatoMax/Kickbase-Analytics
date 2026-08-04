from fastapi import FastAPI
from scrape.fetch import * 
from scrape.scrape_stats import *
from models.predict import get_all_predictions
from optimizer import run_optimizer
from scrape.config import *


app = FastAPI()

LEAGUE_ID = None
TOKEN = None
COOKIES = None


def get_login_info():

    global TOKEN, LEAGUE_ID, COOKIES
    if TOKEN is None or LEAGUE_ID is None or COOKIES is None:
        TOKEN, LEAGUE_ID, COOKIES = login()
    return LEAGUE_ID, TOKEN, COOKIES


#----------------------------------------------------------------------------------------------
# Tab 1: Overview
#----------------------------------------------------------------------------------------------


@app.get("/api/kpi")
def get_kpi():
    league_id, token, cookies = get_login_info()
    budget = get_budget(league_id, token, cookies)
    squad = get_squad(league_id, token, cookies)
    expected_points = int(sum(get_all_predictions(squad).values()))
    return {
        "budget": budget,
        "expected_points": expected_points
    }

@app.get("/api/leaderboard")
def get_leaderboard_endpoint():
    league_id, token, cookies = get_login_info()
    leaderboard = get_leaderboard(league_id, token, cookies)
    return {
        "leaderboard": leaderboard
    }

@app.get("/api/deadline") # Zeit ist in UTC 
def get_deadline():
    current_season = get_season()
    deadline_data = get_kickbase_deadline(current_season, skip_started_matchday=True)

    if not deadline_data:
        return {"matchday": None,
                 "deadline": None
                 }
    
    return {
        "matchday": deadline_data["matchday"],
        "deadline": deadline_data["deadline_utc"]
    }

@app.get("/api/matchups")
def get_matchups():
    current_season = get_season()
    matchday_data = get_data_matchdays(current_season)
    deadline_data = get_kickbase_deadline(current_season, skip_started_matchday=False)
    matchups = get_next_opponents(matchday_data, deadline_data["matchday"])
    next_opponents = [(team, matches[0]["opponent"])  for team, matches in matchups.items() if matches[0]["Heimvorteil"] == 1]

    return {
        "matchups": next_opponents
    }

# Mögliche Erweiterung: Chart was die Punkte der Spieltage in der aktuellen Saison trackt, Leaderboard noch Sachen wie Kaderwert, Punkte letztes Spiel usw. hinzufügen
# Spieler auf dem Transfermarkt welche Kaufempfehlungen haben und bald auslaufen (z.B. nur ca 8h)

#----------------------------------------------------------------------------------------------
# Tab 2: Squad
#----------------------------------------------------------------------------------------------


@app.get("/api/optimized_team")
def optimize_team():

    league_id, token, cookies = get_login_info()

    squad = get_squad(league_id, token, cookies)
    market = get_players_on_market(league_id, token, cookies)
    budget_before = get_budget(league_id, token, cookies)

    players_for_prediction = market + squad
    predictions = get_all_predictions(players_for_prediction)
    optimal_team = run_optimizer(market, squad, budget_before, predictions)

    sum_sells = sum(player["player_price"] for player in optimal_team["sell"])
    sum_buys = sum(player["player_price"] for player in optimal_team["buy"])
    budget_after = budget_before + sum_sells - sum_buys

    kategorien = ["buy", "sell", "hold"]
    for action in kategorien:
        if action in optimal_team:
            for player in optimal_team[action]:
                player["action"] = action

    buy_and_hold_players = optimal_team.get("buy", []) + optimal_team.get("hold", [])
    expected_points = int(sum(player.get("points", 0) for player in buy_and_hold_players))
    
    optimal_team = optimal_team.get("buy", []) + optimal_team.get("sell", []) + optimal_team.get("hold", [])

    return {
        "optimal_team": optimal_team,
        "budget_before": budget_before,
        "budget_after": budget_after,
        "expected_points": expected_points
    }

@app.get("/api/squad")
def get_squad_endpoint():
    league_id, token, cookies = get_login_info()
    squad = get_squad(league_id, token, cookies)
    predictions = get_all_predictions(squad)
    expected_points = int(sum(predictions.values()))
    return {
        "squad": squad,
        "expected_points": expected_points
    }


#----------------------------------------------------------------------------------------------
# Tab 3: transfer market
#----------------------------------------------------------------------------------------------

@app.get("/api/market")
def get_transfer_market():
    league_id, token, cookies = get_login_info()
    market = get_players_on_market(league_id, token, cookies)
    predictions = get_all_predictions(market)

    squad = get_squad(league_id, token, cookies)
    budget = get_budget(league_id, token, cookies)
    optimized = run_optimizer(market, squad, budget, predictions)
    buys_market = [str(player["player_id"]) for player in optimized.get("buy", [])]

    matchdays = get_data_matchdays(get_season())
    deadline = get_kickbase_deadline(get_season())
    current_md = deadline["matchday"] if deadline else None
    opponents = get_next_opponents(matchdays, current_md)

    for player in market:
        player_id = str(player["player_id"])
        team_id = str(player["team_id"])

        player["predicted_points"] = int(predictions.get(player_id, 0))
        player["points_per_price"] = player["predicted_points"] / player.get("player_price", 1)
        player["action"] = "buy" if player["player_id"] in buys_market else "/" 

        team_name = KICKBASE_ID_TO_NAME.get(team_id)

        if not team_name:
            player_info = get_player_info(token, cookies, player_id)
            team_name = player_info.get("team_name")
            if team_name:
                add_if_team_mapping_dont_exists(team_id, team_name)

        next_opponents = opponents.get(team_name, []) if team_name else []
        result = ""
        for opponent in next_opponents:
            team_name = opponent.get("opponent")
            home_advantage = opponent.get("Heimvorteil")
            home_away = "(H)" if home_advantage == 1 else "(A)"
            result += f"{team_name} {home_away}, "
        player["next_opponent"] = result.rstrip(", ")

    return {
        "market": market
    }

@app.post("/api/buy_player/{player_id}/{price}")
def buy_player(player_id, price):
    league_id, token, cookies = get_login_info()
    url = f"{API_URL}/leagues/{league_id}/market/{player_id}/offers"
    payload = {"price": int(price)}
    response = requests.post(url, headers={"tkn": token, "Accept": "application/json"}, cookies=cookies, json=payload)

    if response.status_code == 200:
        return {"status": "success", "message": f"Gebot für {player_id} platziert."}
    else:
        return {"status": "error", "detail": response.text}


# todo: 
# mehr try except Blöcke einbauen für mögliche Fehler
# mehr Kommentare für besseres Verständnis einfügen
# Backups und Schutzmechanismen für die Datenbanken anlegen. Historische Daten können nicht zurückgeholt werden
# prüfen ob irgendwo nach TeamID gesucht wird in team_mapping ohne hinzufügen von neuen TeamIDs