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

    button_refresh = st.button("Refresh")
    
    df_squad = df_players[df_players["Action"] != "buy"]
    df_squad.reset_index(drop=True, inplace=True)
    styled_squad = df_squad.style.apply(lambda row: highlight_rows(row, "sell"), axis=1)

    edited_cur_squad = st.data_editor(
        styled_squad, height="content", width="stretch", hide_index=True,
        disabled=["Name", "Position", "Team", "Price", "Expires", "Predicted Points", "Action", "Next Opponents"], 
        column_config={"player_id": None, "team_id": None, "expires": None, "checkbox": st.column_config.CheckboxColumn(
                    "Sell",
                    help="Check if you want to sell this player",
                    default=False)})

    
    sell_button = st.button("Sell Players")

    sold_players = st.session_state.get("sold_players", [])
    errors_during_sale = st.session_state.get("errors_during_sale", [])

    for player in errors_during_sale:
        st.error(f"Error selling {player[0]}: {player[1]}.")
    for player in sold_players:
        st.success(f"Successfully sold {player}.")

    if "sold_players" in st.session_state:
        del st.session_state["sold_players"]
    if "errors_during_sale" in st.session_state:
        del st.session_state["errors_during_sale"]


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




    

session_state_params = ["optimized_team", "budget_before", "budget_after", "expected_points_optimized", "expected_points_current"]

if button_refresh:
    for param in session_state_params:
        if param in st.session_state:
            del st.session_state[param] 
    st.rerun()

if sell_button:
    df = edited_cur_squad
    players_to_sell = df[df["checkbox"] == True]

    sold_players = []
    errors_during_sale = []
    for index, row in players_to_sell.iterrows():
        player_id = row["player_id"]
        player_name = row["Name"]
        response = sell_player(player_id)
        
        if response["status"] == "success":
            sold_players.append(player_name)
        else:
            errors_during_sale.append((player_name, response.get("detail", "Unknown error")))

    st.session_state["sold_players"] = sold_players
    st.session_state["errors_during_sale"] = errors_during_sale
    
    for param in session_state_params:
        if param in st.session_state:
            del st.session_state[param] 
    st.rerun()    


# Auf Spieler klicken und danach öffnet sich Pop-Up mit Spielerstats und wieso diese Punkte vorhergesagt wurden
# Knopf um automatisch alle Spieler in die Startelf zu packen (vorraussetzung nur 11 Spieler im kader, ggf. Lösung wenn man mehr als 11 hat, prüfen ob überhaupt möglich)
# wenn man mehr als 11 Spieler im Kader hat, sind die expected Points höher als bei optimized_squad, maybe separat berechnen wenn man optimized nur auf dem Kader anwendet und die Spieler mit "hold" 
# Größe aktuellem Kader über dem Dataframe anzeigen
# Option verkauf von Spieler zu blocken also das Spieler als unverkäuflich betrachtet werden, sofern es nicht rausgenommen wird und immer in optimized_squad bleibt
# Sicherheitsmechanismus beim Verkauf von Spielern, welche nicht als sell verkauft sind
