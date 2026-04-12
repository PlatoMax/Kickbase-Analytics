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


# Pipeline to fill the team databases

# teams:
li_teams = fetch_ligainsider_teams()
kb_teams = get_all_teams_kickbase(token, cookies)
# print(li_teams)
# print(kb_teams)

for team in kb_teams:
    team_name_kb = team["team_name"]
    team_name_li = TEAMS_MAPPING[team_name_kb]

    team_id = team["team_id"]
    
    save_teams(team_id, team_name_kb, li_teams[team_name_li])
    total_entries_databank += 1

#teams_stats:















end_time = time.perf_counter()
dauer_in_minuten = (end_time - start_time) / 60
print(f"Fertig! Es wurden {total_entries_databank} Einträge in {dauer_in_minuten:.2f} Minuten gespeichert.")


# Add in Player performance his team in that match
# try einabuen bei Checks in den Dictonaries für Daten aus der vergangenheit, z.B. VFL-Bochum aus letztem Jahr nicht im Dictonary

# mehr try except Blöcke einbauen für mögliche Fehler
# Teams Datenbank für jeden Spieltag Infos scrapen + in DB schreiben