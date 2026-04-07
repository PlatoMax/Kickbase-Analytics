import time
from scrape.getIDs import *
from scrape.config import API_URL
from scrape.fetch import login
from scrape.scrape_stats import *
from database import *
import sqlite3
from scrape.getIDs import fetch_ligainsider_players

start_time = time.perf_counter()
total_entries_databank = 0

token, league_id, cookies = login()

spielername = "Bischof"
neuer_id, neuer_pos = get_player_id_and_position_kickbase(token, cookies, spielername)
print(f"Kickbase-ID von {spielername}: {neuer_id}")

print(get_market_value_at_date(get_player_market_values(token, cookies, neuer_id), "2026-04-05"))

player_info = get_player_info(token, cookies, neuer_id)
print(get_player_info(token, cookies, neuer_id))
name = player_info["name"]
team_id = player_info["team"]
print("Name: ", name, " Team ID:" , team_id)

season = "2024/2025"
stats_kickbase = get_player_performance_kb(token, cookies, neuer_id, team_id, season)
print(stats_kickbase)

# print(kb_season_to_openLiga_season(season))
openL_season = kb_season_to_openLiga_season(season)
# kb_season = openLiga_season_to_kb_season(openL_season)

matchday = 28
data_matchdays = get_data_matchdays("2025")
next_opponents = get_next_opponents(data_matchdays, matchday)
clean_data = clean_matchdays(data_matchdays)
team_tracker = calculate_table(clean_data, matchday)
table = create_table(team_tracker)
teams_form = get_current_form(clean_data, matchday)
cur_matchday = merge_team_stats(table, next_opponents, teams_form)
min_match = min_matchday(clean_data)



position = 3
# stats_ligainsider = scrape_player_stats_LI(spielername, position, season)       
# goals_and_grades = get_player_goals_and_grades(spielername, season)
# print(merge_all_stats(stats_kickbase, stats_ligainsider, goals_and_grades, position))

# list_ligainsider = fetch_ligainsider_players()
# print(get_all_teams_kickbase(token, cookies))
# list_kickbase = fetch_kickbase_players(token, cookies)


#conn = sqlite3.connect('kickbase.db')
#cursor = conn.cursor()
#cursor.execute("SELECT name FROM players")
#spieler_in_db = cursor.fetchall()
#for tupel_name in spieler_in_db: 
#    clear_name = tupel_name[0]
#    player_id, player_position = get_player_id_and_position(token, cookies, clear_name)
#    if player_id is None:
#       print(f'Spielername {clear_name} nicht in Kickbase vorhanden')

# create_tables()
# matches = match_players(list_kickbase, list_ligainsider, ALIAS_MAP, TEAMS_MAPPING)
# clear_players()
# save_players(matches)






end_time = time.perf_counter()
dauer_in_minuten = (end_time - start_time) / 60
print(f"Fertig! Es wurden {total_entries_databank} Einträge in {dauer_in_minuten:.2f} Minuten gespeichert.")


# Add in Player performance his team in that match
# try einabuen bei Checks in den Dictonaries für Daten aus der vergangenheit, z.B. VFL-Bochum aus letztem Jahr nicht im Dictonary

# mehr try except Blöcke einbauen für mögliche Fehler
# Teams Datenbank für jeden Spieltag Infos scrapen + in DB schreiben