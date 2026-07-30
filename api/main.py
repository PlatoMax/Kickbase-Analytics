from fastapi import FastAPI
from scrape.fetch import * 
from scrape.scrape_stats import get_squad, get_players_on_market, get_budget
from models.predict import get_all_predictions
from optimizer import run_optimizer
from scrape.config import *


app = FastAPI()

TOKEN = None
LEAGUE_ID = None
COOKIES = None


def get_login_info():

    global TOKEN, LEAGUE_ID, COOKIES
    if TOKEN is None or LEAGUE_ID is None or COOKIES is None:
        TOKEN, LEAGUE_ID, COOKIES = login()
    return TOKEN, LEAGUE_ID, COOKIES

#----------------------------------------------------------------------------------------------
# Tab 1: Overview
#----------------------------------------------------------------------------------------------
@app.get("/api/kpi")
def get_kpi():
    token, league_id, cookies = get_login_info()
    budget = get_budget(token, league_id, cookies)
    squad = get_squad(token, league_id, cookies)
    expected_points = sum(get_all_predictions(squad).values())
    return {
        "budget": budget,
        "expected_points": expected_points
    }

@app.get("/api/leaderboard")
def get_leaderboard_endpoint():
    token, league_id, cookies = get_login_info()
    leaderboard = get_leaderboard(token, league_id, cookies)
    return {
        "leaderboard": leaderboard
    }

#----------------------------------------------------------------------------------------------
# Tab 2: Squad
#----------------------------------------------------------------------------------------------


@app.get("/api/optimized_team")
def optimize_team():

    token, league_id, cookies = get_login_info()

    squad = get_squad(league_id, token, cookies)
    market = get_players_on_market(league_id, token, cookies)
    budget = get_budget(league_id, token, cookies)

    players_for_prediction = market + squad
    predictions = get_all_predictions(players_for_prediction)
    optimal_team = run_optimizer(market_players=market, squad_players=squad, budget=budget, predictions=predictions)

    return {
        "status": "success",
        "optimal_team": optimal_team,
        "budget": budget
    }




# todo: 
# mehr try except Blöcke einbauen für mögliche Fehler
# mehr Kommentare für besseres Verständnis einfügen
# Backups und Schutzmechanismen für die Datenbanken anlegen. Historische Daten können nicht zurückgeholt werden