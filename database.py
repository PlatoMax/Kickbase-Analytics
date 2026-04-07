import sqlite3

def get_connection():
    conn = sqlite3.connect("kickbase.db")
    return conn

def create_tables(): 
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            link_onefootball TEXT,
            link_liga_insider TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Teamname TEXT,
            Tabellenplatz INTEGER,
            matchday INTEGER,
            season TEXT,
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
            form_match_5_Heimvorteil INTEGER
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
            team2 INTEGER,
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
            
            FOREIGN KEY (player_id) REFERENCES players(id)
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
            team2 INTEGER,
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
            
            FOREIGN KEY (player_id) REFERENCES players(id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tabellen erstellt!")

def save_teams(name, link_onefootball, link_liga_insider): 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO teams (name, link_onefootball, link_liga_insider)
                   VALUES (?, ?, ?)
                   """, (name, link_onefootball, link_liga_insider))
    conn.commit()
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
            points_per_minute, points_per_value, team1, team2,
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
            :points_per_minute, :points_per_value, :team1, :team2,
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
            points_per_minute, points_per_value, team1, team2,
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
            :points_per_minute, :points_per_value, :team1, :team2,
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
    """
    
    cursor.execute(sql, stat_to_insert)
    
    conn.commit()
    conn.close()


def get_last_matchday_fieldplayer(player_id):
    '''In Datenbank schauen was der letzte Spieltag war, Output: (date, season)'''
    conn = sqlite3.connect('kickbase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, season FROM player_stats_field WHERE player_id = ? ORDER BY date DESC LIMIT 1", (player_id))
    result = cursor.fetchone()
    if result:
        return result[0], result[1]  # [date, season]
    else:
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
    

