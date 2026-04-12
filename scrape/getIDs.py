import requests
from bs4 import BeautifulSoup
import unicodedata
from rapidfuzz import fuzz
from scrape.config import API_URL


TEAMS_MAPPING = { 
#   Kickbase: Ligainsider
    "Bayern": "FC Bayern München",
    "Dortmund": "Borussia Dortmund",
    "Hoffenheim": "TSG Hoffenheim",
    "Stuttgart": "VfB Stuttgart",
    "Leipzig": "RB Leipzig",
    "Leverkusen": "Bayer 04 Leverkusen",
    "Frankfurt": "Eintracht Frankfurt",
    "Freiburg": "SC Freiburg",
    "Union Berlin": "1. FC Union Berlin",
    "Augsburg": "FC Augsburg",
    "Hamburg": "Hamburger SV",
    "M'gladbach": "Borussia Mönchengladbach",
    "Mainz": "1. FSV Mainz 05",
    "Köln": "1. FC Köln",
    "Bremen": "SV Werder Bremen",
    "St. Pauli": "FC St. Pauli", 
    "Wolfsburg": "VfL Wolfsburg",
    "Heidenheim": "1. FC Heidenheim",
}

ALIAS_MAP = {
    # Can be used if the current logic don´t fidn a match betweeen the Kickbase an LigaInsider name. 
    # structure:
    # Name Kickbase : Name LigaInsider
}

def get_player_id_and_position_kickbase(token, cookies, name):
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



# updated Version jeden Spieler in Datenbank eintragen
# verwendete Quellen: Kickbase, LigaInsider.
# Ebene 1: Namen normalizieren
# Ebene 2: Alias Map
# Ebene 3: Fuzzy-Matching
# Ebene 4: Bei Fehlschlag Name in Liste speichern für spätere Analyse was das Problem ist

#fetch Funktionen, Output für jeden Spieler ein Dict mit: {"source": "ligainsider" oder "kickbase", "original_name": "Min-jae Kim","normalized_name": "minjae kim",
#    "team_name": "FC Bayern", "link": "https://...", Für Kickbase: "id": "12345","position": "Abwehr" }


def get_all_teams_kickbase(token, cookies):
    """Alle Teams aus der Tabelle bekommen"""

    teams = []
    url = f"{API_URL}/competitions/1/table"
    response = requests.get(
        url,
        headers={"tkn": token, "Accept": "application/json"},
        cookies=cookies)
    
    if(response.status_code != 200):
        print(f"Request get_all_teams fehlgeschlagen. Fehlercode: {response.status_code}")
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
    teams = get_all_teams_kickbase(token, cookies)
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
    

def fetch_ligainsider_teams():
    '''Holt alle Teams aus Ligainsider'''
    urlInsider = "https://www.ligainsider.de/bundesliga/tabelle/"
    sourceInsider = requests.get(urlInsider)
    
    if sourceInsider.status_code != 200:
        print(f'Fehler bei request Anfrage. status_code = {sourceInsider.status_code}')
        return []
        
    soupInsider = BeautifulSoup(sourceInsider.text, 'html.parser')
    li_teams = {}

    # Tabelle nutzen um alle Teams und deren Teamlinks zu holen
    for team in soupInsider.find_all('tr', class_="table_row"):
        team_column = team.find('td', class_="title_column2")
        team_element = team_column.find('span').find('a')
        
        teamName = team_element.get_text()
        teamlink = f"https://www.ligainsider.de" + team_element.get("href") + "kader/"
        
        li_teams[teamName] = teamlink
            
    return li_teams
                

def fetch_ligainsider_players(li_teams):
    '''Holt alle Spieler aus Ligainsider'''
    players = []

    for team in li_teams:
        teamName = team["team_name"]
        teamlink = team["link_liga_insider"] 
        
        team_req = requests.get(teamlink)
        if team_req.status_code != 200:
            print(f"Kader von {teamName} konnte nicht geladen werden.")
            continue 
            
        soup_team = BeautifulSoup(team_req.text, 'html.parser')
        
        for player in soup_team.find_all('div', class_="middle_info_box"):
            if not player.find('a'):
                continue 
                
            if not player.find('span') or not player.find('strong'):
                continue 
                
            player_link = f"https://www.ligainsider.de" + player.find('a').get("href")
            
            firstNameInsider = player.find('span').get_text().strip()
            lastNameInsider = player.find('strong').get_text().strip()
            nameInsider = f"{firstNameInsider} {lastNameInsider}"
            
            normalized_name = normalize_Name(nameInsider) # Achtung: Stelle sicher, dass die Funktion importiert/vorhanden ist
            
            players.append({
                "source": "ligainsider", 
                "original_name": nameInsider,
                "normalized_name": normalized_name,
                "team_name": teamName, 
                "link": player_link 
            })
            
    return players

def match_players(list_kickbase, list_ligainsider, ALIAS_MAP, TEAMS_MAPPING): 
    '''Erstellt Matching zwischhen den verschiedenen Quellen'''
    matches = []
    for player_kb in list_kickbase:
        matched_li_player = None
        name_kb = player_kb["player_name"]
        normalized_name_kb = player_kb["normalized_name"]
        team_kb = player_kb["team_name"]
        team_li = TEAMS_MAPPING[team_kb]

        if name_kb in ALIAS_MAP: # Level 3: Alias Map
                name_li = ALIAS_MAP[name_kb]
                print(f"Match gefunden in Alias Map! Kickbase: {name_kb}, Ligainsider: {name_li} \n\n") #\n\n just for the debugging to see easilier if it works
                matched_li_player = name_li

        filtered_players_li = []
        filtered_players_li = [player_li for player_li in list_ligainsider if player_li["team_name"] == team_li]

        

        for cur in filtered_players_li: 
            normalized_name_li = cur["normalized_name"]
        
            if normalized_name_li in normalized_name_kb: # Level 2: Namen normalisiert sind gleich
                matched_li_player = cur
            
            else: # Level 1, Fuzzy
                score_fuzzy = fuzz.partial_ratio(normalized_name_kb, normalized_name_li)
                if(score_fuzzy > 80):
                    matched_li_player = cur

        if matched_li_player: 
                # print("Match gefunden, Name KB: ", name_kb, " Name LI: ", cur["original_name"])
                matches.append({
                    "kickbase_id": player_kb["player_id"],
                    "name": name_kb,
                    "team_name": team_kb,
                    "team_id": player_kb["team_id"],
                    "position": player_kb["position"],
                    "link_liga_insider": matched_li_player["link"]
                })

        else: 
            print(f'{name_kb} nicht gefunden. Normalized: {normalized_name_kb} Team: {team_kb} \n\n\n') #3x \n just so you can find the missmatches in the terminal
    return matches