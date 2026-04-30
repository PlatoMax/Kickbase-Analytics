import pandas as pd
import sqlite3
import numpy as np


# Get Player_stats_field und Goalkeeper 
def get_df_field(): 
    conn = sqlite3.connect("kickbase.db")

    query_field_players = "SELECT * FROM player_stats_field"

    df_field_players = pd.read_sql_query(query_field_players, conn)

    conn.close()

    df_field_players = df_field_players.sort_values(by=['player_id', 'season', 'matchday']).reset_index(drop=True)   
    # Spieler ohne Spielzeit nicht ins Trainigsset aufnehmen (erstmal zum testen der Auswirkungen)
    df_field_players = df_field_players[df_field_players["minutes"] > 0] 
    return df_field_players

def get_df_gk():
    conn = sqlite3.connect("kickbase.db")
    query_goalkeeper = "SELECT * FROM player_stats_gk"
    df_goalkeeper = pd.read_sql_query(query_goalkeeper, conn)
    conn.close()
    df_goalkeeper = df_goalkeeper.sort_values(by=['player_id', 'season', 'matchday']).reset_index(drop=True)
    # Spieler ohne Spielzeit nicht ins Trainigsset aufnehmen (erstmal zum testen der Auswirkungen)
    df_goalkeeper = df_goalkeeper[df_goalkeeper["minutes"] > 0] 
    return df_goalkeeper

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

def sums(df, sum_cols):
    df["cards_total"] = df["yellow_cards"].fillna(0) + df["yellow_red_cards"].fillna(0) * 2 + df["red_cards"].fillna(0) * 3

    current_sum_cols = sum_cols + ["cards_total"]

    for col in current_sum_cols:
        df[f"{col}_sum_last_5"] = (
            df.groupby(["player_id", "season"])[col]
            .shift(1).rolling(window=5).sum().fillna(0)
        )
        
    df = df.drop(columns=["cards_total"])
    return df


def create_target_variable(df):
    df["target_points"] = df.groupby(["player_id", "season"])["points"].shift(-1)

    return df

#---------------------------------------------------------------------------------------------------------------------------------
# Pipeline playerstats


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
    "points_per_value",
    "ligaInsider_points"           
]

sum_cols_field = ["goals", "assists"]

efficiency_cols_gk = [
    "paraden",
    "fehler_vor_gegentor"

]

ratio_pairs_gk = [
    ("abgewehrte_schuesse", "abgewehrte_schuesse_gesamt"),
    ("strafraum_beherrschung", "strafraum_beherrschung_gesamt"),
    ("abgewehrte_elfmeter", "elfmeter_gesamt"),
    ("grosschancen_pariert", "grosschancen_gesamt")
]

form_trend_cols = [
    "goals_own_team", 
    "goals_enemy_team", 
    "match_result", 
    "grade",
    "points_per_value"            
]

sum_cols_gk = [
    "weisse_weste"
]


def process_data(df_field_players, df_goalkeeper): 
    df_field_players = points_avg_and_trend(df_field_players)
    df_field_players = minutes_avg_and_trend(df_field_players)
    df_field_players = points_p90(df_field_players)
    df_field_players = p90(df_field_players, efficiency_cols_field)
    df_field_players = ratios(df_field_players, ratio_pairs_field)
    df_field_players = form_trends(df_field_players, form_trend_cols)
    df_field_players = sums(df_field_players, sum_cols_field)
    df_field_players = create_target_variable(df_field_players)

    df_goalkeeper = points_avg_and_trend(df_goalkeeper)
    df_goalkeeper = minutes_avg_and_trend(df_goalkeeper)
    df_goalkeeper = points_p90(df_goalkeeper)
    df_goalkeeper = p90(df_goalkeeper, efficiency_cols_gk)
    df_goalkeeper = ratios(df_goalkeeper, ratio_pairs_gk)
    df_goalkeeper = form_trends(df_goalkeeper, form_trend_cols)
    df_goalkeeper = sums(df_goalkeeper, sum_cols_gk)
    df_goalkeeper = create_target_variable(df_goalkeeper)

    return df_field_players, df_goalkeeper


# Merge mit Team_stats
def get_final_ml_data():
    df_field_players = get_df_field()
    df_goalkeeper = get_df_gk()

    df_field_players["market_value"] = pd.to_numeric(df_field_players["market_value"], errors="coerce") # vorher ein String gewesen

    df_field_players, df_goalkeeper = process_data(df_field_players, df_goalkeeper)
    
    
    df_field_players = df_field_players.dropna(subset=["target_points"])
    df_goalkeeper = df_goalkeeper.dropna(subset=["target_points"])

    conn = sqlite3.connect("kickbase.db")
    query_team_stats = "SELECT * FROM team_stats"
    df_team_stats = pd.read_sql_query(query_team_stats, conn)
    conn.close()

    df_team_stats = df_team_stats.sort_values(by=["team_name", "season", "matchday"])  

    df_field_players = pd.merge(
        df_field_players,
        df_team_stats,
        how="left",
        on=["season", "matchday", "team_name"],
        suffixes=("", "_team"),
    )

    df_field_players = pd.merge(
        df_field_players,
        df_team_stats,
        how="left",
        left_on=["season", "matchday", "opponent_name"],
        right_on=["season", "matchday", "team_name"],
        suffixes=("", "_opponent"),
    )

    drop_cols_field = [
        "id",
        "player_id",
        "team_name",
        "opponent_name",
        "date",
        "points",
        "minutes",
        "goals_own_team",
        "goals_enemy_team",
        "match_result",
        "goals",
        "assists",
        "yellow_cards",
        "yellow_red_cards",
        "red_cards",
        "ligaInsider_points",
        "grade",
        "status",
        "erfolgreiche_paesse",
        "paesse_gesamt",
        "gewonnene_zweikaempfe",
        "gewonnene_zweikaempfe_gesamt",
        "gewonnene_luftkaempfe",
        "gewonnene_luftkaempfe_gesamt",
        "erfolgreiche_tacklings",
        "tacklings_gesamt",
        "begangene_fouls",
        "geklaerte_baelle",
        "abgefangene_baelle",
        "balleroberungen",
        "ballverluste",
        "erfolgreiche_dribblings",
        "dribblings_gesamt",
        "torschuss_vorlagen",
        "kreierte_grosschancen",
        "schuesse_aufs_tor",
        "schussgenauigkeit",
        "schussgenauigkeit_gesamt",
        "fehler_vor_gegentor",
        "geblockte_baelle",
        "team_name_team",
        "team_name_opponent",
        "id_team",
        "id_opponent",
        "points_per_minute"
    ]

    drop_cols_opponent = [col for col in df_field_players.columns if "opponent_1" in col or "opponent_2" in col or "opponent_3" in col]

    df_field_players = df_field_players.drop(columns=drop_cols_field, errors="ignore")
    df_field_players = df_field_players.drop(columns=drop_cols_opponent, errors="ignore")

    # Analog: Merge Teamstats mit df_goalkeeper Goalkeeper und droppe Rohspalten
    df_goalkeeper = pd.merge(
        df_goalkeeper,
        df_team_stats,
        how="left",
        on=["season", "matchday", "team_name"],
        suffixes=("", "_team"),
    )

    df_goalkeeper = pd.merge(
        df_goalkeeper,
        df_team_stats,
        how="left",
        left_on=["season", "matchday", "opponent_name"],
        right_on=["season", "matchday", "team_name"],
        suffixes=("", "_opponent"),
    )

    drop_cols_gk = [
        "id_opponent",
        "id_team",
        "id",
        "player_id",
        "team_name",
        "opponent_name",
        "date",
        "points",
        "minutes",
        "goals_own_team",
        "goals_enemy_team",
        "match_result",
        "goals",
        "assists",
        "yellow_cards",
        "yellow_red_cards",
        "red_cards",
        "ligaInsider_points",
        "grade",
        "status",
        "team_name_team",
        "team_name_opponent",
        "abgewehrte_schuesse",
        "abgewehrte_schuesse_gesamt",       
        "paraden",
        "weisse_weste",       
        "strafraum_beherrschung",
        "strafraum_beherrschung_gesamt",        
        "abgewehrte_elfmeter",
        "elfmeter_gesamt",
        "grosschancen_pariert",
        "grosschancen_gesamt",
        "fehler_vor_gegentor",
        "points_per_minute"
        
    ]


    df_goalkeeper = df_goalkeeper.drop(columns=drop_cols_gk, errors="ignore")
    df_goalkeeper = df_goalkeeper.drop(columns=drop_cols_opponent, errors="ignore")

    # Zeige Formen der DataFrames
    print("df_field_players: ", df_field_players.shape)
    print("df_goalkeeper: ", df_goalkeeper.shape)

    return df_field_players, df_goalkeeper
