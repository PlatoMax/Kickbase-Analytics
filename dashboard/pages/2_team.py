import streamlit as st
from components.api import *
import pandas as pd
from components.tables import *

st.set_page_config(page_title="My Team", layout="wide")

if "optimized_team" not in st.session_state:
    optimized_team_data = fetch_optimized_team()
    optimized_team = optimized_team_data["optimal_team"]
    budget_before = optimized_team_data["budget_before"]
    budget_after = optimized_team_data["budget_after"]
    expected_points_optimized = optimized_team_data["expected_points"]

    st.session_state["optimized_team"] = optimized_team
    st.session_state["budget_before"] = budget_before
    st.session_state["budget_after"] = budget_after
    st.session_state["expected_points_optimized"] = expected_points_optimized
    expected_points_current = int(sum(player.get("points", 0) for player in st.session_state["optimized_team"] if player.get("action") != "buy"))
    st.session_state["expected_points_current"] = expected_points_current

df_players = get_table("current_team", st.session_state["optimized_team"])

col1, col2 = st.columns(2)
with col1:
    st.subheader("Current Squad")
    st.metric(label="Current Budget", value=f"{st.session_state['budget_before']:,}€".replace(",", "."))
    st.metric(label="Expected Points", value=st.session_state["expected_points_current"])


    
    df_squad = df_players[df_players["Action"] != "buy"]
    df_squad.reset_index(drop=True, inplace=True)
    styled_squad = df_squad.style.apply(lambda row: highlight_rows(row, "sell"), axis=1)

    edited_cur_squad = st.data_editor(
        styled_squad, height="content", use_container_width=True, hide_index=True,
        disabled=["Name", "Position", "Team", "Price", "Expires", "Predicted Points", "Action", "Next Opponents"], 
        column_config={"player_id": None, "team_id": None, "expires": None, "checkbox": st.column_config.CheckboxColumn(
                    "Sell",
                    help="Check if you want to sell this player",
                    default=False)})
    

# Predicted Points ergänzen in Dataframe einbauen
# action ergänzen für hold und sell sowie rot markieren wer verkauft werden soll

with col2:
    st.subheader("Optimized Team")
    st.metric(label="Budget after changes", value=f"{st.session_state['budget_after']:,}€".replace(",", "."))
    delta_points = st.session_state["expected_points_optimized"] - st.session_state["expected_points_current"]
    st.metric(label="Expected Points", value=st.session_state["expected_points_optimized"], delta=delta_points)
    
    
    df_optimized = df_players[df_players["Action"] != "sell"]
    df_optimized["expires"] = df_optimized["expires"].apply(lambda x: f"{int(x): ,}h {int((x - int(x)) * 60)}m" if pd.notnull(x) else "-")
    df_optimized.rename(columns={"expires": "Expires"}, inplace=True)
    df_optimized.reset_index(drop=True, inplace=True)

    st.data_editor(df_optimized, hide_index=True, height="content",
                   disabled=["Name", "Position", "Team", "Price", "Expires", "Predicted Points", "Points / Price", "Action", "Next Opponents"],
                   column_config={"player_id": None, "team_id": None, "checkbox": None})

# Auf Spieler klicken und danach öffnet sich Pop-Up mit Spielerstats und wieso diese Punkte vorhergesagt wurden
# hier und/oder in Tab 3_market Knopf zum verkaufen von Spielern analog wie buy in Tab 3
# Knopf um automatisch alle Spieler in die Startelf zu packen (vorraussetzung nur 11 Spieler im kader, ggf. Lösung wenn man mehr als 11 hat)
# refresh button 
# wenn man mehr als 11 Spieler im Kader hat, sind die expected Points höher als bei optimized_squad, maybe separat berechnen wenn man optimized nur auf dem Kader anwendet und die Spieler mit "hold" 
# Größe aktuellem Kader über dem Dataframe 
