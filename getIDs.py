# Tool schreiben um ID's der Spieler scrapen
import requests
from bs4 import BeautifulSoup
import json
import re
import unicodedata

from database import clear_teams, save_teams




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
    "mohamed el amine amoura": "mohammed amoura",
    "dimitris giannoulis": "dimitrios giannoulis",
    "kade. anton": "anton kade",
    "emmanouil saliakas": "manolis saliakas",
    "conor metcalfe": "connor metcalfe",
    "leart paqarada": "leart pacarada",
    "philipp mwene": "phillipp mwene",
    "lee jae sung": "jaesung lee",
}

# Onefootball, LigaInsider (currently working on):
#loop for every Team:
urlTeamsOne = "https://onefootball.com/de/wettbewerb/bundesliga-1/tabelle"
urlInsider = "https://www.ligainsider.de/bundesliga/tabelle/"
sourceOne = requests.get(urlTeamsOne)
sourceInsider = requests.get(urlInsider)

if(sourceOne.status_code == 200 and sourceInsider.status_code == 200):
    soupOne = BeautifulSoup(sourceOne.text, 'html.parser')
    soupInsider = BeautifulSoup(sourceInsider.text, 'html.parser')
    
    teamLinksDict = {}
    
    # generate team links based on Names in Onefootball
    for team in soupOne.find_all('a', class_= "Standing_standings__rowGrid__45OOd"):
        teamLinkOne = f"https://onefootball.com" + team.get("href") + "/kader"
        teamName = team.get("aria-label")
        teamLinksDict[teamName] = [teamLinkOne]
    
    # adding Teamlinks LigaInsider
    for team in soupInsider.find_all('tr', class_="table_row"):
        teamColumn = team.find('td', class_="title_column2")
        teamElement = teamColumn.find('span').find('a')
        teamName = teamElement.get_text()
        if(teamName in teamLinksDict):
            teamlinkInsider = f"https://www.ligainsider.de" + teamElement.get("href") + "kader/"
            teamLinksDict[teamName].append(teamlinkInsider)
        elif(teamName =="SV Werder Bremen"):      # SV Werder Bremen different naming
            teamlinkInsider = f"https://www.ligainsider.de" + teamElement.get("href") + "kader/"
            teamLinksDict["Werder Bremen"].append(teamlinkInsider)
        else:
            print(f"{teamName} not found in Dictonary Teamlinks")
        
    clear_teams() # Datenbank mit Teams leeren
    
    for team in teamLinksDict: # Teams in Datenbank speichern 
        if(len(teamLinksDict[team]) == 2):
            save_teams(team, teamLinksDict[team][0], teamLinksDict[team][1])
        else: 
            print(f"{team} has no link for onefootball or ligaInsider")
    
# single Team:
    players = []
    for teamName, links in teamLinksDict.items():
        if(len(links) == 2):
            linkOne = links[0]
            linkInsider = links[1]

            # Onefootball
            playerLinkDict = {}
            soupOne = BeautifulSoup(requests.get(linkOne).text, 'html.parser')
            for player in soupOne.find_all('a', class_="EntityNavigationLink_container__hufgh"):
                name = player.get("aria-label")
                # remove numbers in names:
                name2 = re.sub(r'\s*\(\d+\)', '', name)
                name2 = normalize_Name(name2)
                LinkOnefootball = f"https://onefootball.com/" + player.get("href") + "/stats"
                playerLinkDict[name2] = LinkOnefootball

            # LigaInsider
            
            soupInsider = BeautifulSoup(requests.get(linkInsider).text, 'html.parser')
            for player in soupInsider.find_all('div', class_="middle_info_box"):
                if(player.find_all('a') == []):
                    continue
                else:
                    pLinkIsider = f"https://www.ligainsider.de" + player.find('a').get("href") + "bundesliga_daten/"
                    if(player.find_all('span') == [] or player.find('strong') == []):
                        print(f"{player} not found")
                        continue
                    else:
                
                        firstNameInsider = player.find('span').get_text()
                        lastNameInsider = player.find('strong').get_text()
                        nameInsider = firstNameInsider.strip() + " " + lastNameInsider.strip()
                        
                        # compare names by splitting them into sets of words
                        liCleanName = normalize_Name(nameInsider)
                        liNameSet = set(liCleanName.lower().split())

                        matched = False

                        for ofName in playerLinkDict.keys():
                            compareName = ofName
                            if(compareName in ALIAS_MAP):
                                compareName = ALIAS_MAP[compareName]
                                
                            ofNameSet = set(compareName.split())
                            intersection = ofNameSet.intersection(liNameSet)

                            matched = False

                            if(len(intersection ) >= 2):
                                matched = True
                            elif ofNameSet.issubset(liNameSet) or liNameSet.issubset(ofNameSet):
                                matched = True

                            if(matched):
                                players.append({
                                    "Name": nameInsider, 
                                    "Playerlink Onefootball": playerLinkDict[ofName],
                                    "Teanlink Onefootball" : links[0], 
                                    "Playerlink LigaInsider": pLinkIsider, 
                                    "Teanlink LigaInsider": links[1] 
                                })
                                matched = True
                                break

                        if not matched:
                            print(f"{nameInsider} not found in Dictonary")

    with open("ids.json", "w") as file:
        json.dump(players, file, indent=4)

