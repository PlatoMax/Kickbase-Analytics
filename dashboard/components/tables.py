import streamlit as st
import pandas as pd


if "editor_key" not in st.session_state:
    st.session_state["editor_key"] = 0

def format_euro(x):
    try:
        clean_x = str(x).replace(".", "").replace(",", "")
        if clean_x.isdigit() and int(clean_x) > 0:
            return f"{int(clean_x):,}€".replace(",", ".")
        return ""
    except Exception as e:
        return str(x)

def format_bids():
    current_key = f"market_editor_{st.session_state['editor_key']}"
    changes = st.session_state[current_key]["edited_rows"]
    
    df = st.session_state["market"]
    
    for id, change in changes.items():
        if "Place Bid" in change:
            new_val = change["Place Bid"]
            
            if new_val and "€" not in str(new_val):
                clean_val = str(new_val).replace(".", "").replace(",", "")
                
                if clean_val.isdigit():
                    row_idx = int(id)
                    df.loc[row_idx, "Place Bid"] = format_euro(clean_val)
                    df.loc[row_idx, "place_bid_raw"] = int(clean_val)
            
            elif not new_val:
                row_idx = int(id)
                df.loc[row_idx, "Place Bid"] = ""
                df.loc[row_idx, "place_bid_raw"] = 0
                
    st.session_state["market"] = df
    
    if current_key in st.session_state:
        del st.session_state[current_key]
    st.session_state["editor_key"] += 1

def highlight_rows(row, mode):
    if mode == "buy":
        background_color = "background-color: rgba(46, 204, 113, 0.3)" # green
    elif mode == "sell":
        background_color = "background-color: rgba(231, 76, 60, 0.3)" # red
    
    if row['Action'] == f"{mode}":
        return [background_color] * len(row)
    else:
        return [''] * len(row)

def get_table(mode, data):
    df = pd.DataFrame(data)

    df.reset_index(drop=True, inplace=True)
        
    if "points" in df.columns:
        df["points"] = df["points"].apply(lambda x: f"{int(x): ,}" if pd.notnull(x) else "N/A")
        df.rename(columns={"points": "Predicted Points"}, inplace=True)
        
    elif "predicted_points" in df.columns:
        df["predicted_points"] = df["predicted_points"].apply(lambda x: f"{int(x): ,}" if pd.notnull(x) else "N/A")
        df.rename(columns={"predicted_points": "Predicted Points"}, inplace=True)
    else:
        df["Predicted Points"] = "N/A"

    df["player_price"] = df["player_price"].apply(lambda x: f"{int(x): ,}€".replace(",", "."))

    if mode == "market":
        df["expires"] = df["expires"].apply(lambda x: f"{int(x): ,}h {int((x - int(x)) * 60)}m" if pd.notnull(x) else "-")
        df.sort_values(by=["expires"], inplace=True)

        df["place_bid_raw"] = 0
        df["Place Bid"] = df["place_bid_raw"].apply(lambda x: f"{int(x): ,}€".replace(",", ".") if x > 0 else "") 
        df.rename(columns={"expires": "Expires"}, inplace=True)

    if mode == "current_team":
        df = df.sort_values(by=["player_pos", "team_name", "Playername"])

    if mode == "optimized_team":
        df = df.sort_values(by=["player_pos", "team_name", "Playername"])
        df = df[df["action"] != "sell"]
        df["expires"] = df["expires"].apply(lambda x: f"{int(x): ,}h {int((x - int(x)) * 60)}m" if pd.notnull(x) else "-")

    pos_mapping = {1: "Torwart", 2: "Abwehr", 3: "Mittelfeld", 4: "Angriff"}
    df["player_pos"] = df["player_pos"].map(pos_mapping)

    df["checkbox"] = False

    df.rename(columns={"Playername": "Name", "player_pos": "Position", "team_name": "Team", "player_price": "Price", "predicted_points": "Predicted Points", "points_per_price": "Points / Price", "action": "Action", "next_opponent": "Next Opponents"}, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df