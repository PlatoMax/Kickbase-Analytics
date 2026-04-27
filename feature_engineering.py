import pandas as pd
import sqlite3


conn = sqlite3.connect("kickbase.db")

query = "SELECT * FROM player_stats_field"

df = pd.read_sql_query(query, conn)

conn.close()

df = df.sort_values(by=['player_id', 'season', 'matchday']).reset_index(drop=True)   
    

# Punkte avg letzten 3 und 5 Spiele
df["points_filled"] = df['points'].fillna(0)

df["points_avg_last_3"] = (
    df.groupby(["player_id", "season"])["points_filled"] 
    .shift(1)
    .rolling(window=3)
    .mean()
)

df["points_avg_last_5"] = (
    df.groupby(["player_id", "season"])["points_filled"]
    .shift(1)
    .rolling(window=5)
    .mean()
)

df = df.drop(columns=["points_filled"])

# Trend Punkte
df["points_trend"] = df["points_avg_last_3"] - df["points_avg_last_5"]

# Spielzeit avg letzten 3 und 5 Spiele
df["minutes_filled"] = df["minutes"].fillna(0)

df["minutes_avg_last_3"] = (
    df.groupby(["player_id", "season"])["minutes_filled"]
    .shift(1)
    .rolling(window=3)
    .mean()
)

df["minutes_avg_last_5"] = (
    df.groupby(["player_id", "season"])["minutes_filled"]
    .shift(1)
    .rolling(window=5)
    .mean()
)

# Trend Spielzeit
df["minutes_trend"] = df["minutes_avg_last_3"] - df["minutes_avg_last_5"]

df = df.drop(columns=["minutes_filled"])






