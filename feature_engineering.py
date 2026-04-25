import pandas as pd
import sqlite3


conn = sqlite3.connect("kickbase.db")

query = "SELECT * FROM player_stats_field"

df = pd.read_sql_query(query, conn)

conn.close()

df = df.sort_values(by=["player_id", "season", "matchday"])
    
    

df["points_avg_last_3"] = (
    df.groupby(["player_id", "season"])["points_filled"] 
    .shift(1)
    .rolling(window=3)
    .mean()
)

df = df.drop(columns=["points_filled"])






