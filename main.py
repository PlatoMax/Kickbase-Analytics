import time
from scrape.getIDs import get_player_id_and_position
from scrape.config import API_URL
from scrape.fetch import login
from scrape.scrape_stats import *
from database import get_last_matchday

start_time = time.time()
total_entries_databank = 0

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
season = "2024/2025"
stats_kickbase = get_player_performance_kb(token, cookies, neuer_id, team_id, season)
# print(stats_kickbase)

position = 3
stats_ligainsider = scrape_player_stats_LI(spielername, position, season)
goals_and_grades = get_player_goals_and_grades(spielername, season)
print(merge_all_stats(stats_kickbase, stats_ligainsider, goals_and_grades, position))


end_time = time.time()
dauer_in_minuten = (end_time - start_time) / 60
print(f"Fertig! Es wurden {total_entries_databank} Einträge in {dauer_in_minuten:.2f} Minuten gespeichert.")



# Fall Spieler nicht in Kickbase (bsp. Yannick Eduardo) einbauen
