import pandas as pd
import sqlite3
import numpy as np


# Player_stats_field
conn = sqlite3.connect("kickbase.db")

query_field_players = "SELECT * FROM player_stats_field"
query_goalkeeper = "SELECT * FROM player_stats_gk"

df_field_players = pd.read_sql_query(query_field_players, conn)
df_goalkeeper = pd.read_sql_query(query_goalkeeper, conn)

conn.close()

df_field_players = df_field_players.sort_values(by=['player_id', 'season', 'matchday']).reset_index(drop=True)   
df_goalkeeper = df_goalkeeper.sort_values(by=['player_id', 'season', 'matchday']).reset_index(drop=True)

# Punkte avg und trend letzten 3 und 5 Spiele
def points_avg_and_trend(df):
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
    df["points_trend"] = df["points_avg_last_3"] - df["points_avg_last_5"]
    df = df.drop(columns=["points_filled"])
    return df

# Spielzeit avg letzten 3 und 5 Spiele
def minutes_avg_and_trend(df):
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
    df = df.drop(columns=["minutes_filled"])
    return df



def points_p90(df):
    df["points_p90_last_5"] = (
        (df["points_avg_last_5"] / df["minutes_avg_last_5"]) * 90
    )
    df["points_p90_last_5"] = df["points_p90_last_5"].replace([np.inf, -np.inf], np.nan).fillna(0)  

    df["points_p90_last_3"] = (
    (df["points_avg_last_3"] / df["minutes_avg_last_3"]) * 90
)
    df["points_p90_last_3"] = df["points_p90_last_3"].replace([np.inf, -np.inf], np.nan).fillna(0)  

    return df

# Effizient messen in dem man den avg. * 90 rechnet

def p90(df, efficiency_cols):

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
    
    return df



# Wahrscheinlichkeitsmetriken 
def ratios(df, ratio_pairs):
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

    return df

# Form von Spieler und Team berechnen


def form_trends(df, form_trend_cols):
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

    return df

# Summe für Goals, Assits und Karten
def sums_cards_goals_assists(df):
    df["cards_total"] = df["yellow_cards"].fillna(0) + df["yellow_red_cards"].fillna(0) * 2 + df["red_cards"].fillna(0) * 3

    sum_cols = ["goals", "assists", "cards_total"]

    for col in sum_cols:
        df[f"{col}_sum_last_5"] = (
            df.groupby(["player_id", "season"])[col]
            .shift(1).rolling(window=5).sum().fillna(0)
        )
        
    df = df.drop(columns=["cards_total"])

    return df



efficiency_cols_field = [
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

ratio_pairs_field = [
    ("erfolgreiche_paesse", "paesse_gesamt"), 
    ("gewonnene_zweikaempfe", "gewonnene_zweikaempfe_gesamt"),
    ("gewonnene_luftkaempfe", "gewonnene_luftkaempfe_gesamt"),
    ("erfolgreiche_tacklings", "tacklings_gesamt"),
    ("erfolgreiche_dribblings", "dribblings_gesamt"),
    ("schussgenauigkeit", "schussgenauigkeit_gesamt")
]


form_trend_cols = [
    "goals_own_team", 
    "goals_enemy_team", 
    "match_result", 
    "grade",
    "points_per_value"            
]


df_field_players = points_avg_and_trend(df_field_players)
df_field_players = minutes_avg_and_trend(df_field_players)
df_field_players = points_p90(df_field_players)
df_field_players = p90(df_field_players, efficiency_cols_field)
df_field_players = ratios(df_field_players, ratio_pairs_field)
df_field_players = form_trends(df_field_players, form_trend_cols)
df_field_players = sums_cards_goals_assists(df_field_players)

#---------------------------------------------------------------------------------------------------------------------------------
# Playerstats Goalkeeper
#---------------------------------------------------------------------------------------------------------------------------------

