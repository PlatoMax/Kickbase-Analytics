import joblib
from feature_engineering import *
from database import *
import pandas as pd


model_def = joblib.load("model_Abwehr.pkl")
model_mf = joblib.load("model_Mittelfeld.pkl")
model_off = joblib.load("model_Angriff.pkl")
model_gk = joblib.load("model_gk.pkl")


def get_features(players):
    player_ids_field = [str(player["player_id"]) for player in players if int(player["player_pos"]) != 1]
    player_ids_gk = [str(player["player_id"]) for player in players if int(player["player_pos"]) == 1]

    conn = get_connection()

    df_field = pd.DataFrame()
    if player_ids_field:
        placeholders_field = ", ".join(["?"] * len(player_ids_field))
        query_field = f"""
            SELECT ps.*, p.position AS position, p.kickbase_id AS kickbase_id
            FROM player_stats_field ps
            JOIN players p ON ps.player_id = p.id
            WHERE p.kickbase_id IN ({placeholders_field})
        """
        df_field = pd.read_sql_query(query_field, conn, params=player_ids_field)

    df_gk = pd.DataFrame()
    if player_ids_gk:
        placeholders_gk = ", ".join(["?"] * len(player_ids_gk))
        query_gk = f"""
            SELECT ps.*, 1 AS position, p.kickbase_id AS kickbase_id
            FROM player_stats_gk ps
            JOIN players p ON ps.player_id = p.id
            WHERE p.kickbase_id IN ({placeholders_gk})
        """
        df_gk = pd.read_sql_query(query_gk, conn, params=player_ids_gk)

    conn.close()

    if not df_field.empty:
        df_field = df_field.sort_values(by=['player_id', 'season', 'matchday'], ascending=[True, False, False])
        df_field = df_field.groupby('player_id').head(10).reset_index(drop=True)
        df_field = df_field.sort_values(by=['player_id', 'season', 'matchday'], ascending=[True, True, True])


    if not df_gk.empty:
        df_gk = df_gk.sort_values(by=['player_id', 'season', 'matchday'], ascending=[True, False, False])
        df_gk = df_gk.groupby('player_id').head(10).reset_index(drop=True)
        df_gk = df_gk.sort_values(by=['player_id', 'season', 'matchday'], ascending=[True, True, True])

    df_field = get_final_ml_data(df_field, is_training=False)
    df_gk = get_final_ml_data(df_gk, is_training=False)

    df_def, df_mid, df_off = split_by_position(df_field)

    return df_gk, df_def, df_mid, df_off



def predict(df_features, position):

    if position == 1:
        predictions = model_gk.predict(df_features)
    elif position == 2:
        predictions = model_def.predict(df_features)
    elif position == 3:
       predictions = model_mf.predict(df_features)
    else:
        predictions = model_off.predict(df_features) 

    return predictions


def get_all_predictions(players):

    df_gk, df_def, df_mid, df_off = get_features(players)
    
    results = {}

    def run_predictions_for_df(df, position):
        if df is None or df.empty:
            print("DF ist leer oder none")
            return
        
        id_col = "kickbase_id" if "kickbase_id" in df.columns else "player_id"
        cur_ids = df[id_col].tolist()

        df_predict = df.drop(columns=["player_id", "kickbase_id", "season", "target_points"], errors="ignore")

        predictions = predict(df_predict, position)

        for player_id, prediction in zip(cur_ids, predictions):
            results[player_id] = float(prediction)

    run_predictions_for_df(df_gk, 1)
    run_predictions_for_df(df_def, 2)
    run_predictions_for_df(df_mid, 3)
    run_predictions_for_df(df_off, 4)

    return results