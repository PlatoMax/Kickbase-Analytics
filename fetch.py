import json
import math
from zoneinfo import ZoneInfo
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
import os 


# Anmeldedaten aus .env Datei laden
load_dotenv()
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
api_url = "https://api.kickbase.com/v4"


# Login-Request
response = requests.post(
    "https://api.kickbase.com/v4/user/login",
    json={"em": email, "pass": password, "loy": False, "rep": {}}
)
currentCookies = {"kkstrauth": response.cookies.get("kkstrauth")}

# Token extrahieren
if response.status_code == 200:
    data = response.json()
    token = data.get("tkn")
    leagueId = data["srvl"][0]["id"]

# Spieler auf dem Markt abfragen
PlayerOnMarket = requests.get(
    f"{api_url}/leagues/{leagueId}/market",
    headers={"tkn": token, "Accept":"application/json"}, cookies = currentCookies
)



# Spieler auf dem Transferarkt in JSON speichern
data = PlayerOnMarket.json()
result = []
if PlayerOnMarket.status_code == 200:
    for player in data["it"]:  
        pos = player["pos"]
        if pos == 1:
            pos = "TW"
        elif pos == 2:
            pos = "ABW"
        elif pos == 3:
            pos = "MF"
        elif pos == 4:
            pos = "ST"
        starts = player["prob"]
        if starts == 1:
            starts = "sicher"
        elif starts == 2:
            starts = "wird erwartet"
        elif starts == 3:
            starts = "unsicher"
        elif starts == 4:
            starts = "unwahrscheinlich"
        elif starts == 5:
            starts = "ausgeschlossen"
        mvTrend = player["mvt"]
        if mvTrend > 0:
            mvTrend = "steigend"
        elif mvTrend < 0:
            mvTrend = "fallend"
        else:
            mvTrend = "stabil" 
            
        result.append([player["fn"] + " " + player["n"], player["prc"], math.floor(player["exs"] / 60), player.get("ap",0), pos, starts, mvTrend]) 
sortedResult = sorted(result, key=lambda x: x[2])

with open("currentMarket.json", "w") as file:
    json.dump(sortedResult, file, indent=4)

# mein aktuelles Team abfragen 
myTeam = requests.get(
    f"{api_url}/leagues/{leagueId}/squad",
    headers={"tkn": token, "Accept":"application/json"}, cookies = currentCookies
)
# mein aktuelles Geld abfragen
# Mein Geld plus Geld der anderen Manager
myMoney = requests.get(
    f"{api_url}/leagues/{leagueId}/me/budget",
    headers={"tkn": token, "Accept":"application/json"}, cookies = currentCookies
)
data = myTeam.json()
result = []
for player in data["it"]:  
        pos = player["pos"]
        if pos == 1:
            pos = "TW"
        elif pos == 2:
            pos = "ABW"
        elif pos == 3:
            pos = "MF"
        elif pos == 4:
            pos = "ST"
        starts = player.get("prob", 5)
        if starts == 1:
            starts = "sicher"
        elif starts == 2:
            starts = "wird erwartet"
        elif starts == 3:
            starts = "unsicher"
        elif starts == 4:
            starts = "unwahrscheinlich"
        elif starts == 5:
            starts = "ausgeschlossen"
        mvTrend = player["mvt"]
        if mvTrend > 0:
            mvTrend = "steigend"
        elif mvTrend < 0:
            mvTrend = "fallend"
        else:
            mvTrend = "stabil"    
        result.append([player["n"], player["mv"], player.get("ap",0), pos, starts, mvTrend])
data = myMoney.json()
moneyAfterPurnchase = data.get("pbaa", data["b"])
moneyAfterSells = data["pbas"]
budget = data["b"]
result.append(["Geld nach Käufen % s" %moneyAfterPurnchase, "Geld nach Verkäufen % s" %moneyAfterSells, "aktuelles Budget % s" %budget])

# myTeam und aktuelles Geld in JSON speichern
with open("myTeam.json", "w") as file:
    json.dump(result, file, indent=4)


# ID´s der anderen Manager scrapen (fortsetzten wenn andere zum testen in Liga)
managerIDs = []
manager = requests.get(
    f"{api_url}/leagues/:leagueId/settings/managers",
    headers={"tkn": token, "Accept":"application/json"}, cookies = currentCookies

)



# alle aktuellen Daten von Spielern auf dem Markt plus meinem Team scrapen

# analysieren mittels Decissiontree und in MarktAnalyse.json speichern