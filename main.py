import time
from scrape.getIDs import get_player_id_and_position, get_all_teams, fetch_kickbase_players
from scrape.config import API_URL
from scrape.fetch import login
from scrape.scrape_stats import *
# from database import get_last_matchday
import sqlite3
from scrape.getIDs import fetch_ligainsider_players

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
# print(merge_all_stats(stats_kickbase, stats_ligainsider, goals_and_grades, position))


print(fetch_ligainsider_players())

# print(get_all_teams(token))
# print(fetch_kickbase_players(token, cookies))

#conn = sqlite3.connect('kickbase.db')
#cursor = conn.cursor()
#cursor.execute("SELECT name FROM players")
#spieler_in_db = cursor.fetchall()
#for tupel_name in spieler_in_db: 
#    clear_name = tupel_name[0]
#    player_id, player_position = get_player_id_and_position(token, cookies, clear_name)
#    if player_id is None:
#       print(f'Spielername {clear_name} nicht in Kickbase vorhanden')



end_time = time.time()
dauer_in_minuten = (end_time - start_time) / 60
print(f"Fertig! Es wurden {total_entries_databank} Einträge in {dauer_in_minuten:.2f} Minuten gespeichert.")

# Fall Spieler nicht in Kickbase (bsp. Yannick Eduardo) einbauen -> beim durchiterieren durch die Spiele von Ligainsider einfach prüfen, 
# ob eine Kickbase-ID gefunden wurde. Falls nicht, continue 
# testen wie viele Spieler none als Kickbase-ID zurückgeben