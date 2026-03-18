# Tool schreiben um ID's der Spieler scrapen
import requests
from bs4 import BeautifulSoup
import json
import re
import unicodedata
from scrape.config import API_URL
from database import clear_teams, save_teams, clear_players, save_players, get_team_id_by_name
from scrape.fetch import login

token, league_id, cookies = login()

def get_player_id_and_position(token, cookies, name):
    response = requests.get(
        f"{API_URL}/competitions/1/players/search?query={name}",     # competition_id 1 = Bundesliga
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies
    )
    data = response.json()
    
    if data.get("it"):
        kickbase_id = data["it"][0].get("pi")
        position = data["it"][0].get("pos")
        return kickbase_id, position
    
    return None, None

# remove umlauts and special characters from names (Badé -> Bade)
def normalize_Name(name):
    name = name.lower().replace("-", " ").replace("ł", "l").replace("ø", "o")
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    return name


ALIAS_MAP = {
    "kim min jae": "minjae kim",
    "alex grimaldo": "alejandro grimaldo",
    "ignacio fernandez" : "equi fernández",
    "jeong woo yeong": "wooyeong jeong",
    "chukwubuike adamu": "junior adamu",
    "k. l. hansen": "kristoffer lund",
    "yannick engelhardt": "yannik engelhardt",
    "nathan n`goumou minpole": "nathan ngoumou",
    "manuel pherai": "immanuel pherai",
    "vinicius souza": "vini souza",
    "mohamed el amine amoura": "mohamed amoura",
    "dimitris giannoulis": "dimitrios giannoulis",
    "kade. anton": "anton kade",
    "emmanouil saliakas": "manolis saliakas",
    "conor metcalfe": "connor metcalfe",
    "leart paqarada": "leart pacarada",
    "philipp mwene": "phillipp mwene",
    "lee jae sung": "jaesung lee",
}

# updated Version jeden Spieler in Datenbank eintragen
# verwendete Quellen: Kickbase, LigaInsider.
# Ebene 1: Namen normalizieren
# Ebene 2: Alias Map
# Ebene 3: Fuzzy-Matching
# Ebene 4: Bei Fehlschlag Name in Liste speichern für spätere Analyse was das Problem ist

#fetch Funktionen, Output für jeden Spieler ein Dict mit: {"source": "ligainsider" oder "kickbase", "original_name": "Min-jae Kim","normalized_name": "minjae kim",
#    "team_name": "FC Bayern", "link": "https://...", Für Kickbase: "id": "12345","position": "Abwehr" }


def get_all_teams(token, cookies):
    """Alle Teams aus der Tabelle bekommen"""

    teams = []
    url = f"{API_URL}/competitions/1/table"
    response = requests.get(
        url,
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies)
    
    if(response.status_code != 200):
        print("Request get_all_teams fehlgeschlagen")
        return []
    
    data = response.json()
    
    for team in data['it']:
        team_name = team.get('tn')
        team_id = team.get('tid')
        teams.append({"team_name" : team_name, "team_id" : team_id})

    return teams

def fetch_kickbase_players(token, cookies):
    '''Holt alle Spieler aus Kickbase'''
    players = []
    teams = get_all_teams(token, cookies)

    for team in teams:
        team_name = team.get('team_name')
        team_id = team.get('team_id')
        url = f"{API_URL}/competitions/1/teams/{team_id}/teamprofile"
        response = requests.get(
        url,
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies)
                            
        if(response.status_code != 200):
            print(f'request fehlgeschlagen für Team {team_name}. Statuscode: ', response.status_code)
            continue
        data = response.json()
        for player in data.get('it'):
            player_name = player.get('n')
            normalized_name = normalize_Name(player_name)
            player_id = player.get('i')
            position = player.get('pos')
            players.append({"team_name" : team_name, "team_id" : team_id, "player_name" : player_name, "normalized_name" : normalized_name,
                             "player_id" : player_id, "position" : position})
    return players
    

def fetch_ligainsider_players():
    '''Holt alle Spieler aus Ligainsider'''
    urlInsider = "https://www.ligainsider.de/bundesliga/tabelle/"
    sourceInsider = requests.get(urlInsider)
    
    if sourceInsider.status_code != 200:
        print(f'Fehler bei request Anfrage. status_code = {sourceInsider.status_code}')
        return []
        
    soupInsider = BeautifulSoup(sourceInsider.text, 'html.parser')
    players = []

    # Tabelle nutzen um alle Teams und deren Teamlinks zu holen
    for team in soupInsider.find_all('tr', class_="table_row"):
        team_column = team.find('td', class_="title_column2")
        team_element = team_column.find('span').find('a')
        
        teamName = team_element.get_text()
        teamlink = f"https://www.ligainsider.de" + team_element.get("href") + "kader/"
        
        
        team_req = requests.get(teamlink)
        if team_req.status_code != 200:
            print(f"Kader von {teamName} konnte nicht geladen werden.")
            continue 
            
        soup_team = BeautifulSoup(team_req.text, 'html.parser')
        
        for player in soup_team.find_all('div', class_="middle_info_box"):
            
            if not player.find('a'):
                continue 
                
            if not player.find('span') or not player.find('strong'):
                print(f"Unvollständige HTML-Tags bei einem Spieler von {teamName}")
                continue 
                
            
            player_link = f"https://www.ligainsider.de" + player.find('a').get("href")
            
            firstNameInsider = player.find('span').get_text().strip()
            lastNameInsider = player.find('strong').get_text().strip()
            nameInsider = f"{firstNameInsider} {lastNameInsider}"
            
            normalized_name = normalize_Name(nameInsider)
            
            players.append({
                "source": "ligainsider", 
                "original_name": nameInsider,
                "normalized_name": normalized_name,
                "team_name": teamName, 
                "link": player_link 
            })
            
    return players



def match_players(list_kickbase, list_ligainsider, alias_map):
    '''Erstellt Matching zwischhen den verschiedenen Quellen'''