def get_player_status(row):
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

from datetime import datetime

def get_gameday_number(row):
    gameday_div = row.find('div', class_='data_column_item pull-left')
    if gameday_div:
        gameday = gameday_div.find('strong')
        if gameday:
            return int(gameday.get_text().strip().replace(".", ""))
    return None


def get_min_season():
    current_year = datetime.now().year
    if datetime.now().month >= 8:
        season_start = current_year
    else:
        season_start = current_year - 1
    
    min_year = season_start - 2  # 3 Saisons: aktuelle + 2 davor
    return f"{min_year}/{str(min_year + 1)[-2:]}"

def scrape_player_stats(soup, position):
    min_season = get_min_season()  
    year = soup.find('span', class_='filter-option pull-left').get_text().strip()
    
    if year < min_season:
        print(f"Stats von {year} übersprungen (älter als {min_season})")
        return []

def scrape_player_stats(soup, position):
    
    if position == 1:  # Torwart nochmal prüfen ob wirklich 1 Torwart ist
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
        status = get_player_status(row)
        spieltag_nr = get_gameday_number(row)
        stat = {
            "spieltag": spieltag_nr,
            "status": status,
        }
        
        # Stats nur extrahieren wenn der Spieler gespielt hat
        if status == "startelf":
            values = row.find_all('div', class_='data_column text-center')
            for i, val in enumerate(values):
                span = val.find('span')
                text = span.get_text() if span else "-"
                stat[columns[i]] = text if text != "-" else None
        
        stats.append(stat)

