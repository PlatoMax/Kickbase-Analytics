from datetime import datetime, timedelta
import requests
from scrape.config import API_URL
import sqlite3
from bs4 import BeautifulSoup 
import json
import os

# Ligainsider: 

def safe_int(element):
    if element:
        text = element.get_text().strip()
        return int(text) if text.isdigit() else 0
    return 0

def safe_float(element):
    if element:
        text = element.get_text().strip().replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return 0
    return 0


def get_player_status_LI(row):
    status_div = row.find('div', class_='data_column_right text-center pull-left')
    
    if not status_div:
        return "unbekannt"
    
    # Prüfe ob ein Icon vorhanden ist
    img = status_div.find('img')
    if img:
        src = img.get('src', '')
        if 'verletzung' in src:
            return "verletzt"
        elif 'aufbautraining' in src:
            return "aufbautraining"
        elif 'verbannung' in src:
            return "nicht_beruecksichtigt"
        elif 'fit' in src:
            return "fit_nicht_gespielt"
        elif 'angeschlagen' in src:
            return "angeschlagen"
        elif 'rote-karte' in src:
            return "rot_gesperrt"
        elif 'gelb-rote-karte' in src:
            return "gelbrot_gesperrt"
        elif 'gelbe-karte' in src:
            return "gelb_gesperrt"
        else:
            return "unbekannt"
    
    # Prüfe ob Text vorhanden ist
    span = status_div.find('span')
    if span:
        text = span.get_text().strip()
        if text == "B":
            return "bank"
        else:
            return "startelf"  
    
    return "unbekannt"

def get_gameday_number_LI(row):
    gameday_div = row.find('div', class_='data_column_item pull-left')
    if gameday_div:
        gameday = gameday_div.find('strong')
        if gameday:
            return int(gameday.get_text().strip().replace(".", ""))
    return None


def kickbase_season_to_ligainsider(season_kickbase): # Beispiel: 2025/2026 -> 2025-2026
    return season_kickbase.replace("/", "-") 

def scrape_player_stats_LI(name, position, season_kickbase): 
    season_ligaInsider = kickbase_season_to_ligainsider(season_kickbase)
    conn = sqlite3.connect('kickbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT link_liga_insider FROM players WHERE name = ?", (name,))
    link_tupel = cursor.fetchone() #fetchone returned ein tupel, daher in str umwandeln 
    
    if link_tupel is None:
        print(f'Für Spieler {name} nichts in Datenbank gefunden')
        return []
    
    link_str = link_tupel[0] 
    URL = f'{link_str}bundesliga_daten/saison-{season_ligaInsider}/'
    responose = requests.get(URL)
    if(responose.status_code != 200):
        print(f"Fehler beim Abrufen der Seite für {name} in Saison {season_ligaInsider}")
        return []
    
    soup = BeautifulSoup(responose.text, 'html.parser')

    if position == 1:  # 1 = Torwart 
        columns = [
            "abgewehrte_schuesse", "paraden", "weisse_weste",
            "strafraum_beherrschung", "abgewehrte_elfmeter",
            "grosschancen_pariert", "fehler_vor_gegentor"
        ]
    else:  # Feldspieler 
        columns = [
            "erfolgreiche_paesse", "gewonnene_zweikaempfe",
            "gewonnene_luftkaempfe", "erfolgreiche_tacklings",
            "begangene_fouls", "geklaerte_baelle",
            "abgefangene_baelle", "balleroberungen",
            "ballverluste", "erfolgreiche_dribblings",
            "torschuss_vorlagen", "kreierte_grosschancen",
            "schuesse_aufs_tor", "schussgenauigkeit",
            "fehler_vor_gegentor", "geblockte_baelle"
        ]
    
    # Jeder Spieltag
    rows = soup.find_all('div', class_='data_column_row')
    stats = []
    for row in rows:
        status = get_player_status_LI(row)
        spieltag_nr = get_gameday_number_LI(row)
        stat = {
            "spieltag": spieltag_nr,
            "status": status,
        }
        
        
        values = row.find_all('div', class_='data_column text-center')
        for i, val in enumerate(values):
            if i < len(columns): 
                col_name = columns[i]
                small = val.find('small')
                span = val.find('span')
                
                
                if small: # <small>-Tag (z.B. "(47/56)")
                    text = small.get_text().strip(" ()") 
                    
                    if "/" in text: # Bruch bekommen z.B. bei erfolgreiche Pässe
                        erfolg, gesamt = text.split("/")
                        stat[col_name] = int(erfolg) if erfolg.isdigit() else 0                        
                        stat[f"{col_name}_gesamt"] = int(gesamt) if gesamt.isdigit() else 0
                    else:
                        stat[col_name] = 0
                        stat[f"{col_name}_gesamt"] = 0
                        
                
                elif span: # <span>-Wert (z.B. "2" oder "69%")
                    text = span.get_text().replace("%", "").strip()
                    if text != "-" and text.isdigit():
                        stat[col_name] = int(text)
                    else:
                        stat[col_name] = 0
                else: 
                    stat[col_name] = 0
        
        stats.append(stat)    
    return stats  

def get_player_goals_and_grades(name, season_kickbase):
    season_ligaInsider = kickbase_season_to_ligainsider(season_kickbase)
    conn = sqlite3.connect('kickbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT link_liga_insider FROM players WHERE name = ?", (name,))
    link_tupel = cursor.fetchone() 
    link_str = link_tupel[0] 
    URL = f'{link_str}noten_und_einsatzhistorie/saison-{season_ligaInsider}'
    response = requests.get(URL)
    if response.status_code != 200:
        print(f"Fehler beim Abrufen der Seite für {name} in Saison {season_ligaInsider}")
        return []
    else: 
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('div', class_='column_row')
        data = []
        for row in rows:
            spieltag_div = row.find('div', class_='table_row_no')
            if not spieltag_div:
                continue
            spieltag_text = spieltag_div.get_text().strip()

            # Skip alles außer Bundesliga, d.h. nur Ziffer + Punkt am Anfang, z.B. "1."
            if not (spieltag_text and spieltag_text.replace('.', '').strip().isdigit()):
                continue

            goals = row.find('div', class_='table_col5 pull-left')
            assists = row.find('div', class_='table_col6 pull-left')
            yellow_cards = row.find('div', class_='table_col7 pull-left')
            yellow_red_cards = row.find('div', class_='table_col8 pull-left')
            red_cards = row.find('div', class_='table_col9 pull-left')
            ligaInsider_points = row.find('div', class_='table_col10 pull-left')
            grade = row.find('div', class_='table_col11 pull-left')
            

            # Prüfen ob Note vorhanden
            if grade:
                grade_find = grade.find('small') 
                grade_found = grade_find is not None
                grade_value = safe_float(grade_find) if grade_found else 0  
            else:
                grade_found = False
                grade_value = 0      

            if not grade_found:
                # Bank-Fall: Spieler hat keine Note -> alle Werte 0
                data.append({
                    "spieltag": spieltag_text,
                    "goals": 0,
                    "assists": 0,
                    "yellow_cards": 0,
                    "yellow_red_cards": 0,
                    "red_cards": 0,
                    "ligaInsider_points": 0,
                    "grade": 0,
                    "bank": 1
                })
            else:
                data.append({
                    "spieltag": spieltag_text,
                    "goals": safe_int(goals),
                    "assists": safe_int(assists),
                    "yellow_cards": safe_int(yellow_cards),
                    "yellow_red_cards": safe_int(yellow_red_cards),
                    "red_cards": safe_int(red_cards),
                    "ligaInsider_points": safe_int(ligaInsider_points),
                    "grade": grade_value,
                    "bank": 0
                })
    return data
    
# ---------------------------------------------------------------------------------------------------------------------------
# Kickbase: 

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(CURRENT_DIR, "team_mapping.json")
 
def load_team_mapping():
    if not os.path.exists(MAPPING_FILE):
        return {}
    with open(MAPPING_FILE, "r") as f:
        return json.load(f)
    
def save_team_mapping(mapping):
    with open(MAPPING_FILE, "w") as f:
        json.dump(mapping, f, indent=4)

KICKBASE_ID_TO_NAME = load_team_mapping()
    
def add_if_team_mapping__dont_exists(teamid, teamname): 
    # Wenn Teamid und Teamname bekannt automatisch eintragen falls noch nicht vorhanden. Ideal nach get_player_info
    if teamid not in KICKBASE_ID_TO_NAME:
        KICKBASE_ID_TO_NAME[teamid] = teamname
        save_team_mapping(KICKBASE_ID_TO_NAME)
        print(f"{teamid}: {teamname} erfolgreich gespeichert")

def get_min_season_kickbase(): #letzte zu betrachtende Saison im Kickbase-Format z.B. 2025/2026
    current_year = datetime.now().year
    if datetime.now().month >= 8:
        season_start = current_year
    else:
        season_start = current_year - 1
    
    return f"{season_start-1}/{str(season_start)}"

def get_player_info(token, cookies, player_id):
    response = requests.get(
        f"{API_URL}/competitions/1/players/{player_id}", #/1 für 1. Bundesliga
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )
    
    if response.status_code != 200:
        print(f"Info-Abfrage für Spieler {player_id} fehlgeschlagen!")
        return None
    
    data = response.json()
    firstname = data.get("fn", "")
    lastname = data.get("ln", "")
    name = firstname + " " + lastname
    position = data.get("pos")
    return {
        "name": name,
        "team": data.get("tid"),
        "team_name": data.get("tn"),
        "team_id": data.get("tid"),
        "position": position
    }
    

def get_player_market_values(token, cookies, player_id):
    response = requests.get(
        f"{API_URL}/competitions/1/players/{player_id}/marketvalue/365",
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )
    
    if response.status_code != 200:
        print(f"Marktwert-Abfrage für Spieler {player_id} fehlgeschlagen!")
        return []
    
    data = response.json()
    epoch = datetime(1970, 1, 1)
    
    market_values = []
    for item in data["it"]:
        datum = (epoch + timedelta(days=item["dt"])).date().isoformat()
        market_values.append({
            "date": datum,       
            "mv": item["mv"]     
        })
    
    return market_values  

def get_market_value_at_date(market_values, target_date):
    result = None
    for entry in market_values:
        if entry["date"] <= target_date:
            result = entry["mv"]  
        else:
            break 
    return result
        
def get_player_performance_kb(token, cookies, player_id, team_id, taget_season):
    response = requests.get(
        f"{API_URL}/competitions/1/players/{player_id}/performance",
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )
    
    if response.status_code != 200:
        print(f"Performance-Abfrage für Spieler {player_id} fehlgeschlagen!")
        return []
    market_values = get_player_market_values(token, cookies, player_id)
    data = response.json()
    # print(data, "\n\n\n") # Debug-Ausgabe, um die Struktur der Daten zu überprüfen
    

    performance = []
    
    for season in data["it"]: 
        season_str = season["ti"]
        if season_str != taget_season: 
            continue
            
        historical_team_id = season.get("sid") 
        
        seen_matchdays = set() 

        for game in season["ph"]:
            if game.get("mp") is None: 
                break 
                
            matchday = game.get("day")

            # Duplikate überspringen        
            if matchday in seen_matchdays:
                continue
            seen_matchdays.add(matchday) # Spieltag als "gesehen" markieren

            date = game.get("md")
            point = game.get("p") 
            minutes_str = game.get("mp") 
            minutes = int(minutes_str.replace("'", "")) if minutes_str else 0
            points_per_minute = point / minutes if minutes > 0 else None

            current_market_value = get_market_value_at_date(market_values, date)

            if minutes > 0 and current_market_value is not None and current_market_value > 0:
                points_per_value = point / current_market_value 
            else:
                points_per_value = None

            t1 = str(game.get("t1")) # Teamid Team 1
            t2 = str(game.get("t2")) # Teamid Team 2
            t1g = game.get("t1g") # Tore Team 1
            t2g = game.get("t2g") # Tored Team 2

            for team_id in [t1, t2]:
                if team_id not in KICKBASE_ID_TO_NAME:
                    print(f"Unbekannte Team-ID gefunden: {team_id} in matchday {matchday}") 
                    new_team_name = input(f"Bitte Name von unbekannten Teamid {team_id} oder 'exit' zum abbrechen eingeben: ")

                    if new_team_name.lower() == 'exit':
                        print("Skript wurde manuell abgebrochen.")
                        return
                    KICKBASE_ID_TO_NAME[team_id] = new_team_name
                    save_team_mapping(KICKBASE_ID_TO_NAME)
                    print(f"{team_id}: {new_team_name} gespeichert")

            team1_name = KICKBASE_ID_TO_NAME[t1]
            team2_name = KICKBASE_ID_TO_NAME[t2]

            # historical_team_id falls Transfer stattfand
            own_goals = t1g if historical_team_id == t1 else t2g
            enemy_goals = t2g if historical_team_id == t1 else t1g
            match_result = 1 if own_goals > enemy_goals else -1 if own_goals < enemy_goals else 0 
            # 1 = Sieg, 0 = Unentschieden, -1 = Niederlage
            

            performance.append({
                "season": season_str,
                "matchday": matchday,
                "date": date,
                "points": point,
                "minutes": minutes,
                "points_per_minute": points_per_minute,
                "market_value": current_market_value,
                "points_per_value": points_per_value,
                "team1": t1,
                "team1_name": team1_name,
                "team2_name": team2_name,
                "team2": t2,
                "goals_own_team": own_goals,
                "goals_enemy_team": enemy_goals,
                "match_result": match_result
            })
    return performance

# ----------------------------------------------------------------------------------------------------------------------------
# Daten Kickbase + LigaInsider kombinieren

def merge_all_stats(stats_kickbase, stats_ligainsider, goals_and_grades, position):
    merged_stats = []
    # Ziel: Ein einheitlicher Datensatz pro Spieltag, der alle relevanten Informationen enthält
    for i in range(len(stats_kickbase)): # für jeden Spieltag 
        if(stats_kickbase[i].get("market_value") is None): # Spieltage ohne Marktwert überspringen
                continue
        base_stat = {
            "season": stats_kickbase[i]["season"],
            "matchday": stats_kickbase[i]["matchday"],
            "date": stats_kickbase[i]["date"],
            "points": stats_kickbase[i]["points"],
            "minutes": stats_kickbase[i]["minutes"],
            "points_per_minute": stats_kickbase[i]["points_per_minute"],
            "market_value": stats_kickbase[i]["market_value"],
            "points_per_value": stats_kickbase[i]["points_per_value"],
            "team1": stats_kickbase[i]["team1"],
            "team1_name": stats_kickbase[i]["team1_name"],
            "team2": stats_kickbase[i]["team2"],
            "team2_name": stats_kickbase[i]["team2_name"],
            "goals_own_team": stats_kickbase[i]["goals_own_team"],
            "goals_enemy_team": stats_kickbase[i]["goals_enemy_team"],
            "match_result": stats_kickbase[i]["match_result"],
            "goals": goals_and_grades[i]["goals"],
            "assists": goals_and_grades[i]["assists"],
            "yellow_cards": goals_and_grades[i]["yellow_cards"],
            "yellow_red_cards": goals_and_grades[i]["yellow_red_cards"],
            "red_cards": goals_and_grades[i]["red_cards"],
            "ligaInsider_points": goals_and_grades[i]["ligaInsider_points"],
            "grade": goals_and_grades[i]["grade"],
        }
        if position == 1: # Torwart
            base_stat.update({
                "status": stats_ligainsider[i].get("status", "unbekannt"),
                "abgewehrte_schuesse": stats_ligainsider[i].get("abgewehrte_schuesse", 0),
                "schuesse_gesamt": stats_ligainsider[i].get("abgewehrte_schuesse_gesamt", 0),
                "paraden": stats_ligainsider[i].get("paraden", 0),
                "weisse_weste": stats_ligainsider[i].get("weisse_weste", 0),
                "strafraum_beherrschung": stats_ligainsider[i].get("strafraum_beherrschung", 0),
                "strafraum_beherrschung_gesamt": stats_ligainsider[i].get("strafraum_beherrschung_gesamt", 0),
                "abgewehrte_elfmeter": stats_ligainsider[i].get("abgewehrte_elfmeter", 0),
                "elfmeter_gesamt": stats_ligainsider[i].get("abgewehrte_elfmeter_gesamt", 0),
                "grosschancen_pariert": stats_ligainsider[i].get("grosschancen_pariert", 0),
                "grosschancen_gesamt": stats_ligainsider[i].get("grosschancen_pariert_gesamt", 0),
                "fehler_vor_gegentor": stats_ligainsider[i].get("fehler_vor_gegentor", 0)
            })  
        else: # Feldspieler
            base_stat.update({
                "status": stats_ligainsider[i].get("status", "unbekannt"),
                "erfolgreiche_paesse": stats_ligainsider[i].get("erfolgreiche_paesse", 0),
                "paesse_gesamt": stats_ligainsider[i].get("erfolgreiche_paesse_gesamt", 0),              
                "gewonnene_zweikaempfe": stats_ligainsider[i].get("gewonnene_zweikaempfe", 0),
                "gewonnene_zweikaempfe_gesamt": stats_ligainsider[i].get("gewonnene_zweikaempfe_gesamt", 0),
                "gewonnene_luftkaempfe": stats_ligainsider[i].get("gewonnene_luftkaempfe", 0),
                "gewonnene_luftkaempfe_gesamt": stats_ligainsider[i].get("gewonnene_luftkaempfe_gesamt", 0),
                "erfolgreiche_tacklings": stats_ligainsider[i].get("erfolgreiche_tacklings", 0),
                "tacklings_gesamt": stats_ligainsider[i].get("erfolgreiche_tacklings_gesamt", 0),
                "begangene_fouls": stats_ligainsider[i].get("begangene_fouls", 0),
                "geklaerte_baelle": stats_ligainsider[i].get("geklaerte_baelle", 0),
                "abgefangene_baelle": stats_ligainsider[i].get("abgefangene_baelle", 0),
                "balleroberungen": stats_ligainsider[i].get("balleroberungen", 0),
                "ballverluste": stats_ligainsider[i].get("ballverluste", 0),
                "erfolgreiche_dribblings": stats_ligainsider[i].get("erfolgreiche_dribblings", 0),
                "dribblings_gesamt": stats_ligainsider[i].get("erfolgreiche_dribblings_gesamt", 0),
                "torschuss_vorlagen": stats_ligainsider[i].get("torschuss_vorlagen", 0),
                "kreierte_grosschancen": stats_ligainsider[i].get("kreierte_grosschancen", 0),
                "schuesse_aufs_tor": stats_ligainsider[i].get("schuesse_aufs_tor", 0),
                "schussgenauigkeit": stats_ligainsider[i].get("schussgenauigkeit", 0),
                "schussgenauigkeit_gesamt": stats_ligainsider[i].get("schussgenauigkeit_gesamt", 0),
                "fehler_vor_gegentor": stats_ligainsider[i].get("fehler_vor_gegentor", 0),
                "geblockte_baelle": stats_ligainsider[i].get("geblockte_baelle", 0)
            })
        merged_stats.append(base_stat)
        
    return merged_stats


#---------------------------------------------------------------------------------------------------------------------------------------------------
# Teamstats

# nutzt OpenLigaDB als Quelle für die matchdays
# berechnet jedes mal die komplette Tabelle etc. 

OPENLIGADB_TO_KICKBASE = {
    # OpenLiga : Kickbase
    "FC Bayern München": "Bayern",
    "Borussia Dortmund": "Dortmund",
    "TSG Hoffenheim": "Hoffenheim",
    "VfB Stuttgart": "Stuttgart",
    "RB Leipzig": "Leipzig",
    "Bayer 04 Leverkusen": "Leverkusen",
    "Eintracht Frankfurt": "Frankfurt",
    "SC Freiburg": "Freiburg",
    "1. FC Union Berlin": "Union Berlin",
    "FC Augsburg": "Augsburg",
    "Hamburger SV": "Hamburg",
    "Borussia Mönchengladbach": "M'gladbach",
    "1. FSV Mainz 05": "Mainz",
    "1. FC Köln": "Köln",
    "SV Werder Bremen": "Bremen",
    "FC St. Pauli": "St. Pauli", 
    "VfL Wolfsburg": "Wolfsburg",
    "1. FC Heidenheim 1846": "Heidenheim",
    "Holstein Kiel": "Kiel",
    "VfL Bochum": "Bochum"
}

def kb_season_to_openLiga_season(kb_season):
    open_liga_season = kb_season.split("/")[0]
    return open_liga_season

def openLiga_season_to_kb_season(openLiga_season):
    sec_year = int(openLiga_season) + 1
    kb_season = f"{openLiga_season}/{sec_year}"
    return kb_season

def get_data_matchdays(season): 
    response = requests.get(f"https://api.openligadb.de/getmatchdata/bl1/{season}")

    if response.status_code != 200:
        print("Fehler beim Statuscode für Request create_tables_for_every_matchday", response.status_code)
    
    matchdays = response.json()
    return matchdays

def get_next_opponents(matchdays, current_matchday): 
    '''return dictonary mit jeweils nächsten Gegner und ob Heim oder Auswärtsspiel'''
    opponents = {}
    target_matchday = None
    for match in matchdays:
        if match["group"].get("groupOrderID") > current_matchday:
            target_matchday = match["group"].get("groupOrderID")
            break

    if target_matchday is None: #Edge Case Saison ist vorbei
        return {}
    
    for match in matchdays:
        matchday_number = match["group"].get("groupOrderID")
        
        if matchday_number > target_matchday + 2: # Nach 3 Spielen abbrechen da nur die nächsten 3 Gegner relevant sind
            break
            
        if matchday_number >= target_matchday:
            team1_name = match["team1"]["teamName"]
            team1_name_kb = OPENLIGADB_TO_KICKBASE[team1_name]

            team2_name = match["team2"]["teamName"]
            team2_name_kb = OPENLIGADB_TO_KICKBASE[team2_name]    
    
            if team1_name_kb not in opponents:
                opponents[team1_name_kb] = []
            if team2_name_kb not in opponents:
                opponents[team2_name_kb] = []

            opponents[team1_name_kb].append({
                "opponent": team2_name_kb,
                "Heimvorteil": 1
            })
            opponents[team2_name_kb].append({
                "opponent": team1_name_kb,
                "Heimvorteil": 0
            })
            
    return opponents


def clean_matchdays(matchdays): 
    #relevante Einträge in matchdays: matchDateTime, team1, team2, matchResults
    stats_matchdays = []
    last_seen_matchday = None
    cur_matchday = []
    for match in matchdays:
        new_matchday = False

        if not match["matchIsFinished"]: 
            continue
        
        date = match.get("matchDateTime")
        season = match.get("leagueSeason")
        kb_season = openLiga_season_to_kb_season(season)

        team1_name = match["team1"]["teamName"]
        team1_name_kb = OPENLIGADB_TO_KICKBASE[team1_name]

        team2_name = match["team2"]["teamName"]
        team2_name_kb = OPENLIGADB_TO_KICKBASE[team2_name]

        matchday_number = match["group"].get("groupOrderID")
        if matchday_number != last_seen_matchday:
            new_matchday = True
        
        matchresult = next((result for result in match["matchResults"] if result["resultName"] == "Endergebnis"), None)
        if matchresult:
            goals_team1 = matchresult["pointsTeam1"]
            goals_team2 = matchresult["pointsTeam2"]

        else:
            print(f"Missing Goals in: {match}")
            goals_team1 = 0
            goals_team2 = 0
        
        if goals_team1 > goals_team2:
            points_team1 = 3
            points_team2 = 0
        elif goals_team1 == goals_team2:
            points_team1 = 1
            points_team2 = 1
        else:
            points_team1 = 0
            points_team2 = 3
        
        if new_matchday:
            if cur_matchday:
                stats_matchdays.append(cur_matchday)
            cur_matchday = []
            last_seen_matchday = matchday_number

        cur_matchday.append({
            "season": kb_season,
            "date": date,
            "matchday": matchday_number,
            "team1_name": team1_name_kb,
            "team2_name": team2_name_kb,
            "goals_team1": goals_team1,
            "goals_team2": goals_team2,
            "points_team1": points_team1,
            "points_team2": points_team2
        })
    stats_matchdays.append(cur_matchday)
    return stats_matchdays

def min_matchday(stats_matchdays): # Wegen Marktwerte gehen Spielerstats nur 365 Tage zurück, daher auch Team_stats so drosseln
    last_date = datetime.now() - timedelta(days=365) 
    
    for matchday_list in stats_matchdays:
        if all(datetime.fromisoformat(match["date"]) > last_date for match in matchday_list):
            return matchday_list[0]["matchday"]
    print("Kein passender Spieltage gefunden für min_matchdays")       
    return 34 # Falls nichts gefunden 34, weil es 34 Spieltage gibt -> somit kein Spieltage passend 

def calculate_table(stats_matchdays, matchday_number): 
# erstellt basierend auf Daten von get_data_matchdays die Tabelle bis Spieltag matchday_number (könnte z.B. nach Spieltag 3, 5, 7 oder so sein)
    team_tracker = {}
    abbruch = False
    for matchday in stats_matchdays:
        if abbruch:
            break
        for match in matchday:
            if match["matchday"] > matchday_number:
                abbruch = True
                break
            teamname1 = match.get("team1_name")
            teamname2 = match.get("team2_name")

            if not teamname1 in team_tracker: # stellt sicher, dass das Teeam auch im Dict ist. 
                team_tracker[teamname1] = {"matchday": matchday_number, "season": match.get("season"), "points": 0, "goals": 0, "goals_conceded": 0}

            if not teamname2 in team_tracker:
                team_tracker[teamname2] = {"matchday": matchday_number, "season": match.get("season"), "points": 0, "goals": 0, "goals_conceded": 0}
            
            t1 = team_tracker[teamname1]
            t2 = team_tracker[teamname2]

            t1["points"] += match.get("points_team1", 0)
            t1["goals"] += match.get("goals_team1", 0)
            t1["goals_conceded"] += match.get("goals_team2", 0) 
            
            t2["points"] += match.get("points_team2", 0)
            t2["goals"] += match.get("goals_team2", 0)
            t2["goals_conceded"] += match.get("goals_team1", 0)
 
    return team_tracker

def create_table(team_tracker):
    table = sorted(team_tracker.items(), key=lambda item: (
        item[1]["points"],
        item[1]["goals"] - item[1]["goals_conceded"],
        item[1]["goals"]
    ), 
    reverse=True 
    )
    return table

def get_current_form(stats_matchdays, matchday_number): 
    teams_form = {}
    abbruch = False
    for matchday in stats_matchdays:
        if abbruch:
            break
        for match in matchday:
            if match["matchday"] > matchday_number:
                abbruch = True
                break
            teamname1 = match.get("team1_name")
            teamname2 = match.get("team2_name")

            if not teamname1 in teams_form: # stellt sicher, dass das Team auch im Dict ist. 
                teams_form[teamname1] = []

            if not teamname2 in teams_form:
                teams_form[teamname2] = []
            
            teams_form[teamname1].append({
                "points": match["points_team1"],
                "goals": match["goals_team1"],
                "goals_conceded": match["goals_team2"],
                "Heimvorteil": 1
            })
            teams_form[teamname2].append({
                "points": match["points_team2"],
                "goals": match["goals_team2"],
                "goals_conceded": match["goals_team1"],
                "Heimvorteil": 0

            })
            teams_form[teamname1] = teams_form[teamname1][-5:]
            teams_form[teamname2] = teams_form[teamname2][-5:]
    
    return teams_form

def merge_team_stats(table, next_opponent, current_form):
    merged_results = []
    
    table_lookup = {team_name: {"rank": index + 1, **stats} 
                    for index, (team_name, stats) in enumerate(table)}
                    

    for index, (team_name, table_stats) in enumerate(table):
        team_entry = {
            "Teamname": team_name,
            "Tabellenplatz": index + 1
        }

        team_entry.update(table_stats)
        
        # Nächsten Gegner ergänzen
        team_opponents = next_opponent.get(team_name, [])

        for i in range(1,4):
            if i <= len(team_opponents):
                opp_data = team_opponents[i-1]
                opponent_name = opp_data.get("opponent")

                team_entry[f"opponent_{i}"] = opponent_name
                team_entry[f"opponent_{i}_Heimvorteil"] = opp_data.get("Heimvorteil")
                
                if opponent_name and opponent_name in table_lookup:
                    team_entry[f"opponent_{i}_rank"] = table_lookup[opponent_name]["rank"]
                else:
                    team_entry[f"opponent_{i}_rank"] = None
            else:
                # Case es gibt kein 3 Spiele mehr (zum Ende der Saison)
                team_entry[f"opponent_{i}"] = None
                team_entry[f"opponent_{i}_Heimvorteil"] = None
                team_entry[f"opponent_{i}_rank"] = None
            
        team_form = current_form.get(team_name, [])
        max_form_games = 5

        for match_number in range(1, max_form_games + 1):

            if match_number <= len(team_form):
                match_stats = team_form[-match_number] 
                
                team_entry[f"form_match_{match_number}_points"] = match_stats.get("points")
                team_entry[f"form_match_{match_number}_goals"] = match_stats.get("goals")
                team_entry[f"form_match_{match_number}_goals_conceded"] = match_stats.get("goals_conceded")
                team_entry[f"form_match_{match_number}_Heimvorteil"] = match_stats.get("Heimvorteil")
            else:
                # Platzhalter für Spiele, die es noch nicht gibt
                team_entry[f"form_match_{match_number}_points"] = None
                team_entry[f"form_match_{match_number}_goals"] = None
                team_entry[f"form_match_{match_number}_goals_conceded"] = None
                team_entry[f"form_match_{match_number}_Heimvorteil"] = None
                
        merged_results.append(team_entry)
                
    return merged_results




