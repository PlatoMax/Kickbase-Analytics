from scrape.getIDs import get_player_id_and_position
from scrape.config import API_URL
from scrape.fetch import login
from scrape.scrape_stats import *
token, league_id, cookies = login()

spielername = "Michael Olise"
neuer_id, neuer_pos = get_player_id_and_position(token, cookies, spielername)
# print(f"Kickbase-ID von {spielername}: {neuer_id}")

# print(get_market_value_at_date(get_player_market_values(token, cookies, neuer_id), "2026-03-06"))

player_info = get_player_info(token, cookies, neuer_id)
# print(get_player_info(token, cookies, neuer_id))
name = player_info["name"]
team_id = player_info["team"]
# print("Name: ", name, " Team ID:" , team_id)
stats_kickbase = get_player_performance_kb(token, cookies, neuer_id, team_id, "2025/2026")


# print(kickbase_season_to_ligainsider("2025/2026"))
stats_ligainsider = scrape_player_stats_LI(spielername, 3, "2025/2026")
goals_and_grades = get_player_goals_and_grades(spielername, "2025/2026")
position = 3
print(merge_all_stats(stats_kickbase, stats_ligainsider, goals_and_grades, position))
