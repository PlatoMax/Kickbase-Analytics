import sqlite3

def get_connection():
    conn = sqlite3.connect("kickbase.db")
    return conn

def create_tables(): 
    conn = get_connection()
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
            team_id INTEGER,
            date TEXT,
            table_position INTEGER,
            next_opponent TEXT,
            has_home_game INTEGER,
            has_international_game INTEGER,
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kickbase_id TEXT,
            name TEXT,
            team_id INTEGER,
            position INTEGER,
            link_onefootball TEXT,
            link_liga_insider TEXT,
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            date TEXT,
            market_value REAL,
            avg_points REAL,
            goals INTEGER,
            assists INTEGER,
            avg_passes REAL,
            avg_duels_won REAL,
            yellow_cards INTEGER,
            red_cards INTEGER,
            starts INTEGER,
            avg_minutes REAL,
            is_available INTEGER,
            marketvalue_trend TEXT,
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

def save_players(kickbase_id, name, team_id, position, link_onefootball, link_liga_insider):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                     INSERT INTO players (kickbase_id, name, team_id, position, link_onefootball, link_liga_insider)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (kickbase_id, name, team_id, position, link_onefootball, link_liga_insider))
    conn.commit()
    conn.close()

def clear_players():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players") 
    conn.commit()
    conn.close()

def get_team_id_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM teams WHERE NAME = ?", (name,))
    result = cursor.fetchone()
    conn.close()