from datetime import datetime, timedelta
import requests
from scrape.config import API_URL
import sqlite3
from bs4 import BeautifulSoup 

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
 
def get_min_season_kickbase(): #letzte zu betrachtende Saison im Kickbase-Format z.B. 2025/2026
    current_year = datetime.now().year
    if datetime.now().month >= 8:
        season_start = current_year
    else:
        season_start = current_year - 1
    
    return f"{season_start-1}/{str(season_start)}"

def get_player_info(token, cookies, player_id):
    response = requests.get(
        f"{API_URL}/competitions/1/players/{player_id}",
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
    return {
        "name": name,
        "team": data.get("tid")
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
    # print(data) # Debug-Ausgabe, um die Struktur der Daten zu überprüfen


    performance = []
    for season in data["it"]: # betrachtet die Saison -> für LigaIns Mathing nutzen
        season_str = season["ti"]
        if(season_str != taget_season): # wenn Saison nicht die gesuchte Saison -> nächste Saison betrachten
            continue
        for game in season["ph"]:
            if(game.get("mp") is None): # Wenn kein Eintrag für Spielzeit -> Spiel liegt in Zukunft -> nicht betrachten
                break 
            matchday = game.get("day")
            date = game.get("md")
            point = game.get("p") # wenn nicht gespielt -> none (ggf. einbauen als Check) 
            minutes_str = game.get("mp") # Spielzeit
            minutes = int(minutes_str.replace("'", "")) if minutes_str else 0
            points_per_minute = point / minutes if minutes > 0 else None

            current_market_value = get_market_value_at_date(market_values, date)

            if minutes > 0 and current_market_value is not None and current_market_value > 0:
                points_per_value = point / current_market_value 
            else:
                points_per_value = None

            t1 = game.get("t1")
            t2 = game.get("t2")
            t1g = game.get("t1g")
            t2g = game.get("t2g")

            own_goals = t1g if team_id == t1 else t2g
            enemy_goals = t2g if team_id == t1 else t1g
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
                "team2": t2,
                "goals_own_team": own_goals,
                "goals_enemy_team": enemy_goals,
                "match_result": match_result
            })
    return performance

#-----------------------------------------------------------------------------------------------------------------------------
# Teams

# def get_table_standig_after_matchday(season, matchday):

# def get_next_opponent(team, season, matchday):

# ----------------------------------------------------------------------------------------------------------------------------
# Daten kombinieren

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
            "team2": stats_kickbase[i]["team2"],
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


# für Tabelle und so https://www.openligadb.de nutzen