import time
from datetime import datetime, timedelta
from scrape.getIDs import *
from scrape.config import API_URL
from scrape.fetch import login
from scrape.scrape_stats import *
from database import *
import sqlite3
from scrape.getIDs import fetch_ligainsider_players

total_entries_databank = 0 # just for fun um Anzahl der Einträge in die Datenbank mitzuzählen

create_tables()

def extract_and_save_teamstats(season): #immer als Kickbase Season angeben!
    clear_teams_stats_one_season(season)
    openliga_season = kb_season_to_openLiga_season(season)
    matchday_data = get_data_matchdays(openliga_season)
    clean_data = clean_matchdays(matchday_data)

    first_matchday = min_matchday(clean_data)

    entries_saved = 0 

    for i in range(first_matchday, 35):
        cal_table = calculate_table(clean_data, i)
        table = create_table(cal_table)
        next_opponents = get_next_opponents(matchday_data, i)
        current_form = get_current_form(clean_data, i)

        team_stats = merge_team_stats(table, next_opponents, current_form)
        save_team_stats(team_stats)
        
        entries_saved += 1 
        
    return entries_saved


# Daten holen und in den Datenbanken speichern
start_time = time.perf_counter() # Just for fun um die Dauer zu sehen

token, league_id, cookies = login()



# teams:
li_teams = fetch_ligainsider_teams()
kb_teams = get_all_teams_kickbase(token, cookies)

for team in kb_teams:
    team_name_kb = team["team_name"]
    team_name_li = TEAMS_MAPPING[team_name_kb]

    team_id = team["team_id"]
    link = li_teams.get(team_name_li, None)
    if link is None:
        print("Für Team ", team_name_li, " keinen Link gefunden")

    save_teams(team_id, team_name_kb, link)
    total_entries_databank += 1

#teams_stats:

current_start_year = datetime.now().year
if datetime.now().month < 8:
   current_start_year -= 1

current_season = f"{current_start_year}/{current_start_year + 1}"
last_season = f"{current_start_year - 1}/{current_start_year}"

total_entries_databank += extract_and_save_teamstats(last_season)   # mit last_season muss nur einmalig aufgerufen werden, danach überflüssig
total_entries_databank += extract_and_save_teamstats(current_season)









end_time = time.perf_counter()
dauer_in_minuten = (end_time - start_time) / 60
print(f"Fertig! Es wurden {total_entries_databank} Einträge in {dauer_in_minuten:.2f} Minuten gespeichert.")


# Add in Player performance his team in that match
# try einabuen bei Checks in den Dictonaries für Daten aus der vergangenheit, z.B. VFL-Bochum aus letztem Jahr nicht im Dictonary

# mehr try except Blöcke einbauen für mögliche Fehler
# testen ob Einträge in teams_stats DB richtig sind, einfach mal paar Stichprobenarbeit anschauen
