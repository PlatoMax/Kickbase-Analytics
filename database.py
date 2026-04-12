import sqlite3

def get_connection():
    conn = sqlite3.connect("kickbase.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables(): 
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,  
            name TEXT NOT NULL UNIQUE,
            link_liga_insider TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Teamname TEXT NOT NULL,
            Tabellenplatz INTEGER,
            matchday INTEGER NOT NULL,
            season TEXT NOT NULL,
            points INTEGER,
            goals INTEGER,
            goals_conceded INTEGER,
            
            opponent_1 TEXT,
            opponent_1_Heimvorteil INTEGER,
            opponent_1_rank INTEGER,
            
            opponent_2 TEXT,
            opponent_2_Heimvorteil INTEGER,
            opponent_2_rank INTEGER,
            
            opponent_3 TEXT,
            opponent_3_Heimvorteil INTEGER,
            opponent_3_rank INTEGER,
            
            form_match_1_points INTEGER,
            form_match_1_goals INTEGER,
            form_match_1_goals_conceded INTEGER,
            form_match_1_Heimvorteil INTEGER,
            
            form_match_2_points INTEGER,
            form_match_2_goals INTEGER,
            form_match_2_goals_conceded INTEGER,
            form_match_2_Heimvorteil INTEGER,
            
            form_match_3_points INTEGER,
            form_match_3_goals INTEGER,
            form_match_3_goals_conceded INTEGER,
            form_match_3_Heimvorteil INTEGER,
            
            form_match_4_points INTEGER,
            form_match_4_goals INTEGER,
            form_match_4_goals_conceded INTEGER,
            form_match_4_Heimvorteil INTEGER,
            
            form_match_5_points INTEGER,
            form_match_5_goals INTEGER,
            form_match_5_goals_conceded INTEGER,
            form_match_5_Heimvorteil INTEGER,
            
            UNIQUE(Teamname, season, matchday)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kickbase_id TEXT,
            name TEXT,
            team_name TEXT,
            team_id INTEGER,
            position INTEGER,
            link_liga_insider TEXT,
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats_field (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            season TEXT,
            matchday INTEGER,
            date TEXT,
            points INTEGER,
            minutes INTEGER,
            points_per_minute REAL,
            market_value REAL,
            points_per_value REAL,
            team1 INTEGER,
            team1_name TEXT,
            team2 INTEGER,
            team2_name TEXT,
            goals_own_team INTEGER,
            goals_enemy_team INTEGER,
            match_result INTEGER,
            goals INTEGER,
            assists INTEGER,
            yellow_cards INTEGER,
            yellow_red_cards INTEGER,
            red_cards INTEGER,
            ligaInsider_points INTEGER,
            grade REAL,
            status TEXT,
            
            erfolgreiche_paesse INTEGER,
            paesse_gesamt INTEGER,
            
            gewonnene_zweikaempfe INTEGER,
            gewonnene_zweikaempfe_gesamt INTEGER,
            
            gewonnene_luftkaempfe INTEGER,
            gewonnene_luftkaempfe_gesamt INTEGER,
            
            erfolgreiche_tacklings INTEGER,
            tacklings_gesamt INTEGER,
            
            begangene_fouls INTEGER,
            geklaerte_baelle INTEGER,
            abgefangene_baelle INTEGER,
            balleroberungen INTEGER,
            ballverluste INTEGER,
            
            erfolgreiche_dribblings INTEGER,
            dribblings_gesamt INTEGER,
            
            torschuss_vorlagen INTEGER,
            kreierte_grosschancen INTEGER,
            schuesse_aufs_tor INTEGER,
            
            schussgenauigkeit INTEGER,
            schussgenauigkeit_gesamt INTEGER,
            
            fehler_vor_gegentor INTEGER,
            geblockte_baelle INTEGER,
            
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE(player_id, season, matchday)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats_gk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            season TEXT,
            matchday INTEGER,
            date TEXT,
            points INTEGER,
            minutes INTEGER,
            points_per_minute REAL,
            points_per_value REAL,
            team1 INTEGER,
            team1_name TEXT,
            team2 INTEGER,
            team2_name TEXT,
            goals_own_team INTEGER,
            goals_enemy_team INTEGER,
            match_result INTEGER,
            goals INTEGER,
            assists INTEGER,
            yellow_cards INTEGER,
            yellow_red_cards INTEGER,
            red_cards INTEGER,
            ligaInsider_points INTEGER,
            grade REAL,
            status TEXT,
            
            abgewehrte_schuesse INTEGER,
            abgewehrte_schuesse_gesamt INTEGER,
            
            paraden INTEGER,
            weisse_weste INTEGER,
            
            strafraum_beherrschung INTEGER,
            strafraum_beherrschung_gesamt INTEGER,
            
            abgewehrte_elfmeter INTEGER,
            elfmeter_gesamt INTEGER,
            
            grosschancen_pariert INTEGER,
            grosschancen_gesamt INTEGER,
            
            fehler_vor_gegentor INTEGER,
            
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE(player_id, season, matchday)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tabellen erstellt!")

def save_teams(team_id, name, link_liga_insider):  
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO teams (id, name, link_liga_insider)
        VALUES (?, ?, ?)  
        ON CONFLICT(id) DO UPDATE SET  
            name = excluded.name,      
            link_liga_insider = excluded.link_liga_insider
    """
    try:
        cursor.execute(sql, (team_id, name, link_liga_insider))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Fehler beim Speichern von Team {name}: {e}")
    finally:
        conn.close()

def clear_teams(): 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM teams") 
    conn.commit()
    conn.close()

def get_team_id_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM teams WHERE NAME = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def clear_player_stats_field():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM player_stats_field")
    conn.commit()
    conn.close()

def save_player_stats_field(player_id, stat):
    
    conn = sqlite3.connect('kickbase.db')
    cursor = conn.cursor()
    stat_to_insert = stat.copy()
    stat_to_insert['player_id'] = player_id

    sql = """
        INSERT INTO player_stats_field (
            player_id, season, matchday, date, points, minutes,
            points_per_minute, points_per_value, team1, team1_name, team2, team2_name,
            goals_own_team, goals_enemy_team, match_result, goals,
            assists, yellow_cards, yellow_red_cards, red_cards,
            ligaInsider_points, grade, status,
            erfolgreiche_paesse, paesse_gesamt,
            gewonnene_zweikaempfe, gewonnene_zweikaempfe_gesamt,
            gewonnene_luftkaempfe, gewonnene_luftkaempfe_gesamt,
            erfolgreiche_tacklings, tacklings_gesamt,
            begangene_fouls, geklaerte_baelle, abgefangene_baelle,
            balleroberungen, ballverluste,
            erfolgreiche_dribblings, dribblings_gesamt,
            torschuss_vorlagen, kreierte_grosschancen, schuesse_aufs_tor,
            schussgenauigkeit, schussgenauigkeit_gesamt,
            fehler_vor_gegentor, geblockte_baelle
        ) VALUES (
            :player_id, :season, :matchday, :date, :points, :minutes,
            :points_per_minute, :points_per_value, :team1, :team1_name, :team2, :team2_name,
            :goals_own_team, :goals_enemy_team, :match_result, :goals,
            :assists, :yellow_cards, :yellow_red_cards, :red_cards,
            :ligaInsider_points, :grade, :status,
            :erfolgreiche_paesse, :paesse_gesamt,
            :gewonnene_zweikaempfe, :gewonnene_zweikaempfe_gesamt,
            :gewonnene_luftkaempfe, :gewonnene_luftkaempfe_gesamt,
            :erfolgreiche_tacklings, :tacklings_gesamt,
            :begangene_fouls, :geklaerte_baelle, :abgefangene_baelle,
            :balleroberungen, :ballverluste,
            :erfolgreiche_dribblings, :dribblings_gesamt,
            :torschuss_vorlagen, :kreierte_grosschancen, :schuesse_aufs_tor,
            :schussgenauigkeit, :schussgenauigkeit_gesamt,
            :fehler_vor_gegentor, :geblockte_baelle
        )
        ON CONFLICT(player_id, season, matchday) DO UPDATE SET
            points = excluded.points,
            minutes = excluded.minutes,
            points_per_minute = excluded.points_per_minute,
            points_per_value = excluded.points_per_value,
            goals_own_team = excluded.goals_own_team,
            goals_enemy_team = excluded.goals_enemy_team,
            match_result = excluded.match_result,
            goals = excluded.goals,
            assists = excluded.assists,
            yellow_cards = excluded.yellow_cards,
            yellow_red_cards = excluded.yellow_red_cards,
            red_cards = excluded.red_cards,
            ligaInsider_points = excluded.ligaInsider_points,
            grade = excluded.grade,
            status = excluded.status,
            erfolgreiche_paesse = excluded.erfolgreiche_paesse,
            paesse_gesamt = excluded.paesse_gesamt,
            gewonnene_zweikaempfe = excluded.gewonnene_zweikaempfe,
            gewonnene_zweikaempfe_gesamt = excluded.gewonnene_zweikaempfe_gesamt,
            gewonnene_luftkaempfe = excluded.gewonnene_luftkaempfe,
            gewonnene_luftkaempfe_gesamt = excluded.gewonnene_luftkaempfe_gesamt,
            erfolgreiche_tacklings = excluded.erfolgreiche_tacklings,
            tacklings_gesamt = excluded.tacklings_gesamt,
            begangene_fouls = excluded.begangene_fouls,
            geklaerte_baelle = excluded.geklaerte_baelle,
            abgefangene_baelle = excluded.abgefangene_baelle,
            balleroberungen = excluded.balleroberungen,
            ballverluste = excluded.ballverluste,
            erfolgreiche_dribblings = excluded.erfolgreiche_dribblings,
            dribblings_gesamt = excluded.dribblings_gesamt,
            torschuss_vorlagen = excluded.torschuss_vorlagen,
            kreierte_grosschancen = excluded.kreierte_grosschancen,
            schuesse_aufs_tor = excluded.schuesse_aufs_tor,
            schussgenauigkeit = excluded.schussgenauigkeit,
            schussgenauigkeit_gesamt = excluded.schussgenauigkeit_gesamt,
            fehler_vor_gegentor = excluded.fehler_vor_gegentor,
            geblockte_baelle = excluded.geblockte_baelle
        
    """
    
    cursor.execute(sql, stat_to_insert)
    conn.commit()
    conn.close()   
                     

def clear_player_stats_gk():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM player_stats_gk")
    conn.commit()
    conn.close()

def save_player_stats_gk(player_id, stat):
    conn = sqlite3.connect('kickbase.db')
    cursor = conn.cursor()
    stat_to_insert = stat.copy()
    stat_to_insert['player_id'] = player_id

    sql = """
        INSERT INTO player_stats_gk (
            player_id, season, matchday, date, points, minutes,
            points_per_minute, points_per_value, team1, team1_name, team2, team2_name,
            goals_own_team, goals_enemy_team, match_result, goals,
            assists, yellow_cards, yellow_red_cards, red_cards,
            ligaInsider_points, grade, status,
            abgewehrte_schuesse, abgewehrte_schuesse_gesamt,
            paraden, weisse_weste,
            strafraum_beherrschung, strafraum_beherrschung_gesamt,
            abgewehrte_elfmeter, elfmeter_gesamt,
            grosschancen_pariert, grosschancen_gesamt,
            fehler_vor_gegentor
        ) VALUES (
            :player_id, :season, :matchday, :date, :points, :minutes,
            :points_per_minute, :points_per_value, :team1, :team1_name, :team2, :team2_name,
            :goals_own_team, :goals_enemy_team, :match_result, :goals,
            :assists, :yellow_cards, :yellow_red_cards, :red_cards,
            :ligaInsider_points, :grade, :status,
            :abgewehrte_schuesse, :abgewehrte_schuesse_gesamt,
            :paraden, :weisse_weste,
            :strafraum_beherrschung, :strafraum_beherrschung_gesamt,
            :abgewehrte_elfmeter, :elfmeter_gesamt,
            :grosschancen_pariert, :grosschancen_gesamt,
            :fehler_vor_gegentor
        )
        ON CONFLICT(player_id, season, matchday) DO UPDATE SET
            points = excluded.points,
            minutes = excluded.minutes,
            points_per_minute = excluded.points_per_minute,
            points_per_value = excluded.points_per_value,
            goals_own_team = excluded.goals_own_team,
            goals_enemy_team = excluded.goals_enemy_team,
            match_result = excluded.match_result,
            goals = excluded.goals,
            assists = excluded.assists,
            yellow_cards = excluded.yellow_cards,
            yellow_red_cards = excluded.yellow_red_cards,
            red_cards = excluded.red_cards,
            ligaInsider_points = excluded.ligaInsider_points,
            grade = excluded.grade,
            status = excluded.status,
            abgewehrte_schuesse = excluded.abgewehrte_schuesse,
            abgewehrte_schuesse_gesamt = excluded.abgewehrte_schuesse_gesamt,
            paraden = excluded.paraden,
            weisse_weste = excluded.weisse_weste,
            strafraum_beherrschung = excluded.strafraum_beherrschung,
            strafraum_beherrschung_gesamt = excluded.strafraum_beherrschung_gesamt,
            abgewehrte_elfmeter = excluded.abgewehrte_elfmeter,
            elfmeter_gesamt = excluded.elfmeter_gesamt,
            grosschancen_pariert = excluded.grosschancen_pariert,
            grosschancen_gesamt = excluded.grosschancen_gesamt,
            fehler_vor_gegentor = excluded.fehler_vor_gegentor

    """
    
    
    cursor.execute(sql, stat_to_insert)
    
    conn.commit()
    conn.close()


def get_last_matchday_fieldplayer(player_id):
    '''In Datenbank schauen was der letzte Spieltag war, Output: (date, season)'''
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, season FROM player_stats_field WHERE player_id = ? ORDER BY date DESC LIMIT 1", (player_id,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0], result[1]  # [date, season]
    else:
        conn.close()
        return None, None
    
def get_last_matchday_gk(player_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, season FROM player_stats_gk WHERE player_id = ? ORDER BY date DESC LIMIT 1", (player_id,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0], result[1]  # [date, season]
    else:
        conn.close()
        return None, None
    

def clear_players():
    """Leert die Tabelle komplett, behält aber die Struktur bei."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM players")
        conn.commit() 
        print("Tabelle 'players' wurde erfolgreich für die neue Saison geleert.")
    except sqlite3.Error as e:
        print(f"Fehler beim Leeren der Tabelle: {e}")
    finally:
        conn.close()
    

def save_players(matches): 
    if not matches: 
        print("Keine Matches")
        return 

    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO players (kickbase_id, name, team_name, team_id, position, link_liga_insider)
        VALUES (:kickbase_id, :name, :team_name, :team_id, :position, :link_liga_insider)
        """
    try: 
        cursor.executemany(sql, matches)
        conn.commit()
    
    except sqlite3.Error as e:
        print(f'Fehler beim einfügügen der Spieler: {e}')
    
    finally:
        conn.close()


def save_team_stats(merged_team_stats): 
    # Aufbau: Saison, matchday, points, goals, goals_conceded, Tabellenplatz, next_opponent, Heimvorteil nächstes Spiel, Tabellenplatz Gegner, Tore etc. Gegner, 
    # Form letzten 5 Spiele + Tore etc.   
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO team_stats (
            Teamname, Tabellenplatz, matchday, season, points, goals, goals_conceded, 
            
            opponent_1, opponent_1_Heimvorteil, opponent_1_rank,
            opponent_2, opponent_2_Heimvorteil, opponent_2_rank,
            opponent_3, opponent_3_Heimvorteil, opponent_3_rank,
            
            form_match_1_points, form_match_1_goals, form_match_1_goals_conceded, form_match_1_Heimvorteil, 
            form_match_2_points, form_match_2_goals, form_match_2_goals_conceded, form_match_2_Heimvorteil, 
            form_match_3_points, form_match_3_goals, form_match_3_goals_conceded, form_match_3_Heimvorteil,
            form_match_4_points, form_match_4_goals, form_match_4_goals_conceded, form_match_4_Heimvorteil, 
            form_match_5_points, form_match_5_goals, form_match_5_goals_conceded, form_match_5_Heimvorteil
            
        ) VALUES (
            :Teamname, :Tabellenplatz, :matchday, :season, :points, :goals, :goals_conceded, 
            
            :opponent_1, :opponent_1_Heimvorteil, :opponent_1_rank, 
            :opponent_2, :opponent_2_Heimvorteil, :opponent_2_rank, 
            :opponent_3, :opponent_3_Heimvorteil, :opponent_3_rank, 
            
            :form_match_1_points, :form_match_1_goals, :form_match_1_goals_conceded, :form_match_1_Heimvorteil, 
            :form_match_2_points, :form_match_2_goals, :form_match_2_goals_conceded, :form_match_2_Heimvorteil, 
            :form_match_3_points, :form_match_3_goals, :form_match_3_goals_conceded, :form_match_3_Heimvorteil, 
            :form_match_4_points, :form_match_4_goals, :form_match_4_goals_conceded, :form_match_4_Heimvorteil, 
            :form_match_5_points, :form_match_5_goals, :form_match_5_goals_conceded, :form_match_5_Heimvorteil
        )
        ON CONFLICT(Teamname, season, matchday) DO NOTHING
    """
    try: 
        cursor.executemany(sql, merged_team_stats)
        conn.commit()
    except sqlite3.Error as e:
        print(f'Fehler beim Einfügen der Teamstats: {e}')
    finally:
        conn.close()

def clear_teams_stats_one_season(season): # season hat to be the kickbase Season, e.g. "2025/2026"
    conn = get_connection()
    cursor = conn.cursor()
    try: 
        cursor.execute(" DELETE FROM team_stats WHERE season = ?", (season,))
        conn.commit() 
        print(f"Datenbank team_stats für Saison {season} cleared")
     
    except sqlite3.Error as e:
         print(f"Error beim clearen von team_stats: {e}")
    
    finally: 
        conn.close()
    

