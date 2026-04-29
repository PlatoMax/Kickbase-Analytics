import pandas as pd
import sqlite3
import numpy as np


# Player_stats_field
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


df["points_p90_last_5"] = (
    (df["points_avg_last_5"] / df["minutes_avg_last_5"]) * 90
)

df["points_p90_last_3"] = (
    (df["points_avg_last_3"] / df["minutes_avg_last_3"]) * 90
)

df["points_p90_last_5"] = df["points_p90_last_5"].replace([np.inf, -np.inf], np.nan).fillna(0)
df["points_p90_last_3"] = df["points_p90_last_3"].replace([np.inf, -np.inf], np.nan).fillna(0)


# Effizient messen in dem man den avg. * 90 rechnet
efficiency_cols = [
    "gewonnene_zweikaempfe",
    "schuesse_aufs_tor",
    "torschuss_vorlagen",
    "kreierte_grosschancen",
    "geklaerte_baelle",
    "abgefangene_baelle",
    "balleroberungen",
    "geblockte_baelle",
    "fehler_vor_gegentor",
    "begangene_fouls",
    "ballverluste"
]

for col in efficiency_cols:
    df[f"{col}_filled"] = df[col].fillna(0)

    df[f"{col}_avg_last_3"] = (
        df.groupby(["player_id", "season"])[f"{col}_filled"]
        .shift(1)
        .rolling(window=3)
        .mean()
    )

    df[f"{col}_p90_last_3"] = df[f"{col}_avg_last_3"] / df["minutes_avg_last_3"] * 90
    df[f"{col}_p90_last_3"] = df[f"{col}_p90_last_3"].replace([np.inf, -np.inf], np.nan).fillna(0)  
    
    df = df.drop(columns=[f"{col}_filled", f"{col}_avg_last_3"])



# Wahrscheinlichkeitsmetriken 
ratio_pairs = [
    ("erfolgreiche_paesse", "paesse_gesamt"), 
    ("gewonnene_zweikaempfe", "gewonnene_zweikaempfe_gesamt"),
    ("gewonnene_luftkaempfe", "gewonnene_luftkaempfe_gesamt"),
    ("erfolgreiche_tacklings", "tacklings_gesamt"),
    ("erfolgreiche_dribblings", "dribblings_gesamt"),
    ("schussgenauigkeit", "schussgenauigkeit_gesamt")
]

for succes_col, total_col in ratio_pairs:
    df[f"{succes_col}_filled"] = df[succes_col].fillna(0)
    df[f"{total_col}_filled"] = df[total_col].fillna(0)

    df[f"{succes_col}_sum_last_3"] = (
    df.groupby(["player_id", "season"])[f"{succes_col}_filled"]        
    .shift(1)
    .rolling(window=3)
    .sum()
    )

    df[f"{total_col}_sum_last_3"] = (
    df.groupby(["player_id", "season"])[f"{total_col}_filled"]        
    .shift(1)
    .rolling(window=3)
    .sum()
    )

    df[f"{succes_col}_ratio_last_3"] = df[f"{succes_col}_sum_last_3"] / df[f"{total_col}_sum_last_3"]
    df[f"{succes_col}_ratio_last_3"] = df[f"{succes_col}_ratio_last_3"].replace([np.inf, -np.inf], np.nan).fillna(0)

    df = df.drop(columns=[
        f"{succes_col}_filled",
        f"{succes_col}_sum_last_3",
        f"{total_col}_filled",
        f"{total_col}_sum_last_3"
    ])

# Form von Spieler und Team berechnen
form_trend_cols = [
    "goals_own_team", 
    "goals_enemy_team", 
    "match_result", 
    "grade"             
]

for col in form_trend_cols:
    df[f"{col}_filled"] = df[col].fillna(0)
    
    df[f"{col}_avg_last_3"] = (
        df.groupby(["player_id", "season"])[f"{col}_filled"]
        .shift(1).rolling(window=3).mean()
    )
    
    df[f"{col}_avg_last_5"] = (
        df.groupby(["player_id", "season"])[f"{col}_filled"]
        .shift(1).rolling(window=5).mean()
    )
    
    df[f"{col}_trend"] = df[f"{col}_avg_last_3"] - df[f"{col}_avg_last_5"]
    
    df = df.drop(columns=[f"{col}_filled"])

# Summe für Goals, Assits und Karten
df["cards_total"] = df["yellow_cards"].fillna(0) + df["yellow_red_cards"].fillna(0) * 2 + df["red_cards"].fillna(0) * 3
sum_cols = ["goals", "assists", "cards_total"]

for col in sum_cols:
    df[f"{col}_sum_last_5"] = (
        df.groupby(["player_id", "season"])[col]
        .shift(1).rolling(window=5).sum().fillna(0)
    )
    
df = df.drop(columns=["cards_total"])

#---------------------------------------------------------------------------------------------------------------------------------
# Playerstats Goalkeeper
#---------------------------------------------------------------------------------------------------------------------------------

