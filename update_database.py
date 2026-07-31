import time
from datetime import datetime, timedelta
from scrape.getIDs import *
from scrape.config import API_URL
from scrape.fetch import login, get_season
from scrape.scrape_stats import *
from database import *
from models.predict import get_all_predictions
from optimizer import run_optimizer
import random

total_entries_databank = 0 # just for fun um Anzahl der Einträge in die Datenbank mitzuzählen

create_tables()

def extract_and_save_teamstats(season): #immer als Kickbase Season angeben!
    clear_teams_stats_one_season(season)
    openliga_season = kb_season_to_openLiga_season(season)
    matchday_data = get_data_matchdays(openliga_season)
    clean_data = clean_matchdays(matchday_data)

    if not clean_data:
        return 0
    
    
    first_matchday = min_matchday(clean_data)
    last_matchday = clean_data[-1][0]["matchday"]

    entries_saved = 0 

    for i in range(first_matchday, last_matchday + 1):
        cal_table = calculate_table(clean_data, i)
        table = create_table(cal_table)
        next_opponents = get_next_opponents(matchday_data, i)
        current_form = get_current_form(clean_data, i)

        team_stats = merge_team_stats(table, next_opponents, current_form)
        save_team_stats(team_stats)

        entries_saved += len(team_stats) 
    print("succesfully saved team_stats für season, ", season)
    return entries_saved

def extract_and_save_playerstats(player, season):
    db_id = player[0]
    player_id = player[1]
    name = player[2]
    position = int(player[5])
    link = player[6]
    
    stats_kickbase = get_player_performance_kb(token, cookies, player_id, season)
    stats_ligainsider = scrape_player_stats_LI(name, position, season, link)
    goals_grades= get_player_goals_and_grades(name, season, link)

    if not stats_kickbase and not stats_ligainsider:
        return 0

    merged_stats = merge_all_stats(stats_kickbase, stats_ligainsider, goals_grades, position)
    
    if position == 1: # pos 1 = GK
        print(f"{name} wegen Position {position} in gk stats gespeichert") # für debugging
        save_player_stats_gk(db_id, merged_stats)
    else:
        print(f"{name} wegen Position {position} in field stats gespeichert") # für debugging
        save_player_stats_field(db_id, merged_stats) 

    return len(merged_stats) #return nur um zu messen wie viele Einträge in der Datenbank gespeichert werden, hat keinen Nutzen und kann entfernt werden

def get_current_kickbase_matchday(token, cookies, player_id, target_season):
    response = requests.get(
        f"{API_URL}/competitions/1/players/{player_id}/performance",
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )
    
    if response.status_code != 200:
        print("Konnte aktuellen Spieltag nicht abrufen! (Status Code Error)")
        return 0
        
    data = response.json()
    matchdays = []
    
    for season in data.get("it", []): 
        season_str = season.get("ti")
        if season_str != target_season or season.get("n") != "Bundesliga": 
            continue

        for game in season.get("ph", []):
            if game.get("mp") is None: 
                break 
            matchdays.append(game.get("day"))

        return matchdays[-1] if matchdays else 0
        
    return 0

# Daten holen und in den Datenbanken speichern
start_time = time.perf_counter() # Just for fun um die Dauer zu sehen

token, league_id, cookies = login()

create_tables()

# teams:
li_teams = fetch_ligainsider_teams()
kb_teams = get_all_teams_kickbase(token, cookies)

for team in kb_teams:
    team_name_kb = team["team_name"]
    team_name_li = TEAMS_MAPPING[team_name_kb]

    team_id = int(team["team_id"])
    link = li_teams.get(team_name_li, None)
    if link is None:
        print("Für Team ", team_name_li, " keinen Link gefunden")

    save_teams(team_id, team_name_kb, link)
    total_entries_databank += 1

#teams_stats:


cur_start_year = get_season()
last_start_year = get_season(last=True)

current_season = f"{cur_start_year}/{cur_start_year + 1}"
last_season = f"{last_start_year}/{last_start_year + 1}"

# total_entries_databank += extract_and_save_teamstats(last_season)   # mit last_season muss nur einmalig aufgerufen werden, danach überflüssig
total_entries_databank += extract_and_save_teamstats(current_season)


# Players

players_kb = fetch_kickbase_players(token, cookies, kb_teams)
players_li = fetch_ligainsider_players(li_teams)
matches = match_players(players_kb, players_li, ALIAS_MAP, TEAMS_MAPPING)
save_players(matches)
total_entries_databank += len(matches)



# Players stats
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM players")

conn.commit()
players = cursor.fetchall()
# Aufbau bei Return: (Datenbank ID, Kickbase-ID, name, team_name, team_id, position, link_liga_insider) 

cursor.execute(f"SELECT max(matchday) FROM player_stats_field WHERE season = '{current_season}'")
latest_matchday_db = cursor.fetchone()
latest_matchday_db = latest_matchday_db[0] if latest_matchday_db[0] is not None else 0
conn.close()

random_player_id = players[0][1]
latest_matchday_kickbase = get_current_kickbase_matchday(token, cookies, random_player_id, current_season) # hier nochmal genauer schauen ob das zukunftssicher ist

print(f"latest db: {latest_matchday_db}, latest kb: {latest_matchday_kickbase}")
max_retries = 5
if latest_matchday_db < int(latest_matchday_kickbase):
    for i, player in enumerate(players): 

        if i % 50 == 0 and i != 0:
            pause = random.uniform(40, 100)
            print(f"Kaffeepause! Skript pausiert für {pause:.0f} Sekunden...")
            time.sleep(pause)

        for attempt in range(max_retries):
            try:
                entries_current = extract_and_save_playerstats(player, current_season)
                time.sleep(random.uniform(1, 2))
                # entries_last = extract_and_save_playerstats(player, last_season) # nur einmal mit last_season runnen, danach überflüssig
                
                total_entries_databank += entries_current # + entires_last sofern entires_last nicht auskommentiert wurde
                # total_entries_databank += entries_last # + entires_last sofern entires_last nicht auskommentiert wurde

                print(f"{player[2]} erfolgreich verarbeitet! (+{entries_current} Einträge)") 
                break # break gilt für attempt Schleife
            except Exception as e: 
                print(f"Warnung bei {player[2]} (Versuch {attempt + 1}/{max_retries}): {e}")    
                
                if attempt < max_retries - 1:
                    sleep_time = random.uniform(5, 10) * (2 ** attempt)
                    print(f"Warte {sleep_time} Sekunden, bevor es nochmal versucht wird...")
                    time.sleep(sleep_time)
                else:
                    print(f"\033[91m Fehler: {player[2]} endgültig übersprungen nach {max_retries} Versuchen. \033[0m ")   

        print(f"{i + 1} von {len(players)} Spieler abgeschlossen")
        time.sleep(random.uniform(2,4))            
else: 
    print("Database ist auf dem neusten Stand")

end_time = time.perf_counter()
dauer_in_minuten = (end_time - start_time) / 60
print(f"Fertig! Es wurden {total_entries_databank} Einträge in {dauer_in_minuten:.2f} Minuten gespeichert.")
