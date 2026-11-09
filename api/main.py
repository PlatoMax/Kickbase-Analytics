from fastapi import FastAPI
from scrape.fetch import * 
from scrape.scrape_stats import *
from models.predict import get_all_predictions
from optimizer import run_optimizer
from scrape.config import *
from datetime import datetime, timezone

app = FastAPI()

TOKEN, LEAGUE_ID, COOKIES = login()

kb_session = requests.Session()
kb_session.headers.update({
    "tkn": TOKEN,
    "Accept": "application/json",
})
kb_session.cookies.update(COOKIES)

def filter_by_deadline(market, squad, deadline):
    predictions = get_all_predictions(market + squad)
    now = datetime.now(timezone.utc)

    hours_until_deadline = (
        (deadline["deadline_utc"] - now).total_seconds() / 3600 
        if deadline and deadline.get("deadline_utc") 
        else None
    )

    if hours_until_deadline is not None:
        market_copy = [
            p for p in market 
            if p.get("expires") is not None and p["expires"] < hours_until_deadline
        ]
    else:
        market_copy = market.copy()

    valid_ids = {str(p["player_id"]) for p in market_copy + squad}
    predictions_copy = {
        pid: pts for pid, pts in predictions.items() 
        if pid in valid_ids
    }
    
    return market_copy, predictions_copy, predictions

#----------------------------------------------------------------------------------------------
# Tab 1: Overview
#----------------------------------------------------------------------------------------------


@app.get("/api/kpi")
def get_kpi():
    budget = get_budget(LEAGUE_ID, TOKEN, COOKIES)
    squad = get_squad(LEAGUE_ID, TOKEN, COOKIES)
    expected_points = int(sum(get_all_predictions(squad).values()))
    return {
        "budget": budget,
        "expected_points": expected_points
    }

@app.get("/api/leaderboard")
def get_leaderboard_endpoint():
    leaderboard = get_leaderboard(LEAGUE_ID, TOKEN, COOKIES)
    return {
        "leaderboard": leaderboard
    }

@app.get("/api/deadline") # Zeit ist in UTC 
def get_deadline():
    current_season = get_season()
    deadline_data = get_kickbase_deadline(current_season, skip_started_matchday=True)

    if not deadline_data:
        return {"matchday": None,
                 "deadline": None,
                    "is_ongoing": None
                 }
    
    return {
        "matchday": deadline_data["matchday"],
        "deadline": deadline_data["deadline_utc"],
        "is_ongoing": deadline_data["is_ongoing"]
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
def optimize_team(only_own_players: bool = False):
    """
    Optimize the team by finding the best combination of players to buy, sell, and hold.
    """
    squad = get_squad(LEAGUE_ID, TOKEN, COOKIES)
    
    if only_own_players:
        market = []
    else:
        market = get_players_on_market(LEAGUE_ID, session=kb_session)

    budget_before = get_budget(LEAGUE_ID, TOKEN, COOKIES)


    deadline = get_kickbase_deadline(get_season())

    market_copy, predictions_copy, _ = filter_by_deadline(market, squad, deadline)
    optimal_team = run_optimizer(market_copy, squad, budget_before, predictions_copy)

    sum_sells = sum(player["player_price"] for player in optimal_team["sell"])
    sum_buys = sum(player["player_price"] for player in optimal_team["buy"])
    budget_after = budget_before + sum_sells - sum_buys

    kategorien = ["buy", "sell", "hold"]
    for action in kategorien:
        if action in optimal_team:
            for player in optimal_team[action]:
                player["action"] = action
                player.setdefault("expires", None)

    buy_and_hold_players = optimal_team.get("buy", []) + optimal_team.get("hold", [])
    expected_points = int(sum(player.get("points", 0) for player in buy_and_hold_players))
    
    optimal_team = optimal_team.get("buy", []) + optimal_team.get("sell", []) + optimal_team.get("hold", [])

    return {
        "optimal_team": optimal_team,
        "budget_before": budget_before,
        "budget_after": budget_after,
        "expected_points": expected_points
    }

@app.post("/api/sell_player/{player_id}")
def sell_player(player_id):
    url = f"{API_URL}/leagues/{LEAGUE_ID}/market/{player_id}/sell"
    response = requests.post(url, headers={"tkn": TOKEN, "Accept": "application/json"}, cookies=COOKIES)

    if response.status_code == 200:
        return {"status": "success"}
    else:
        return {"status": "error", "detail": response.text}

#----------------------------------------------------------------------------------------------
# Tab 3: transfer market
#----------------------------------------------------------------------------------------------

@app.get("/api/market")
def get_transfer_market():

    matchdays = get_data_matchdays(get_season())
    deadline = get_kickbase_deadline(get_season())
    current_md = deadline["matchday"] if deadline else None
    opponents = get_next_opponents(matchdays, current_md)

    market = get_players_on_market(LEAGUE_ID, session=kb_session)
    squad = get_squad(LEAGUE_ID, TOKEN, COOKIES)
    budget = get_budget(LEAGUE_ID, TOKEN, COOKIES)

    market_copy, predictions_copy, predictions = filter_by_deadline(market, squad, deadline)

    optimized = run_optimizer(market_copy, squad, budget, predictions_copy)
    buys_market = [str(player["player_id"]) for player in optimized.get("buy", [])]

    for player in market:
        player_id = str(player["player_id"])
        team_id = str(player["team_id"])

        player["predicted_points"] = int(predictions.get(player_id, 0))
        player["points_per_price"] = player["predicted_points"] / player.get("player_price", 1)
        player["action"] = "buy" if player["player_id"] in buys_market else "/" 

        team_name = KICKBASE_ID_TO_NAME.get(team_id)

        if not team_name:
            player_info = get_player_info(TOKEN, COOKIES, player_id)
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
    url = f"{API_URL}/leagues/{LEAGUE_ID}/market/{player_id}/offers"
    payload = {"price": int(price)}
    response = requests.post(url, headers={"tkn": TOKEN, "Accept": "application/json"}, cookies=COOKIES, json=payload)

    if response.status_code == 200:
        return {"status": "success", "message": f"Gebot für {player_id} platziert."}
    else:
        return {"status": "error", "detail": response.text}


# todo: 
# mehr Kommentare für besseres Verständnis einfügen
# Backups und Schutzmechanismen für die Datenbanken anlegen. Historische Daten können nicht zurückgeholt werden
# prüfen ob irgendwo nach TeamID gesucht wird in team_mapping ohne hinzufügen von neuen TeamIDs
# Lösung suchen für Fall Datenbank muss befüllt werden aber man will schon Dashboard nutzen mit verfügbaren Features (auch wenn nicht vollständig)
# ReadME anpassen
# Bei API Requests prüfen ob man das beschleunigen kann, Anzahl requests reduzueren da oft in verschiedenen Funktionen die gleichen Daten abgefragt werden 