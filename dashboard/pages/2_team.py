import streamlit as st
from components.api import *
import pandas as pd

st.set_page_config(page_title="My Team", layout="wide")

squad = fetch_squad()
optimized_team_data = fetch_optimized_team()
optimized_team = optimized_team_data["optimal_team"]
budget_before = optimized_team_data["budget_before"]
budget_after = optimized_team_data["budget_after"]
expected_points_current = squad["expected_points"]
expected_points_optimized = optimized_team_data["expected_points"]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Current Squad")
    st.metric(label="Current Budget", value=f"{budget_before:,}€".replace(",", "."))
    st.metric(label="Expected Points", value=expected_points_current)

    df_squad = pd.DataFrame(squad["squad"])
    df_squad = df_squad.sort_values(by=["player_pos", "team_name", "Playername"])
    df_squad = df_squad.drop(columns=["player_id","team_id"])
    df_squad["player_price"] = df_squad["player_price"].apply(lambda x: f"{int(x): ,}€".replace(",", "."))

    pos_mapping = {1: "Torwart", 2: "Abwehr", 3: "Mittelfeld", 4: "Angriff"}
    df_squad["player_pos"] = df_squad["player_pos"].map(pos_mapping)

    df_squad = df_squad.rename(columns={"Playername": "Name", "player_pos": "Position", "team_name": "Team"})

    st.dataframe(df_squad, hide_index=True, height="content")


# Predicted Points ergänzen in Dataframe einbauen
# action ergänzen für hold und sell sowie rot markieren wer verkauft werden soll

with col2:
    st.subheader("Optimized Team")
    st.metric(label="Budget after changes", value=f"{budget_after:,}€".replace(",", "."))

    delta_points = expected_points_optimized - expected_points_current
    st.metric(label="Expected Points", value=expected_points_optimized, delta=delta_points)

    df_optimized = pd.DataFrame(optimized_team)
    df_optimized = df_optimized.sort_values(by=["player_pos", "team_name", "Playername"])
    df_optimized = df_optimized.drop(columns=["player_id","team_id"])
    df_optimized = df_optimized[df_optimized["action"] != "sell"]
    df_optimized["player_price"] = df_optimized["player_price"].apply(lambda x: f"{int(x): ,}€".replace(",", "."))
    df_optimized["expires"] = df_optimized["expires"].apply(lambda x: f"{int(x): ,}h {int((x - int(x)) * 60)}m" if pd.notnull(x) else "-")
    df_optimized["points"] = df_optimized["points"].apply(lambda x: f"{int(x): ,}" if pd.notnull(x) else "N/A")

    pos_mapping = {1: "Torwart", 2: "Abwehr", 3: "Mittelfeld", 4: "Angriff"}
    df_optimized["player_pos"] = df_optimized["player_pos"].map(pos_mapping)

    df_optimized = df_optimized.rename(columns={"Playername": "Name", "player_pos": "Position",  "team_name": "Team", "player_price": "Price","expires": "Expires", "points": "Predicted Points", "action": "Action"})

    st.dataframe(df_optimized, hide_index=True, height="content")

# Auf Spieler klicken und danach öffnet sich Pop-Up mit Spielerstats und wieso diese Punkte vorhergesagt wurden
# hier und/oder in Tab 2 Knopf zum verkaufen von Spielern analog wie buy in Tab 3