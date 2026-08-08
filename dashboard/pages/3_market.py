import streamlit as st
from components.api import *
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

def highlight_buy_rows(row):
    if row['Action'] == 'buy':
        return ['background-color: rgba(46, 204, 113, 0.3)'] * len(row)
    else:
        return [''] * len(row)

####################
# DF
####################

st.set_page_config(page_title="Transfer Market", layout="wide")

if "market" not in st.session_state:
    market = fetch_market()
    df_market = pd.DataFrame(market["market"])

    df_market["player_price"] = df_market["player_price"].apply(lambda x: f"{int(x): ,}€".replace(",", "."))
    df_market.sort_values(by=["expires"], inplace=True)
    df_market.reset_index(drop=True, inplace=True)
    df_market["expires"] = df_market["expires"].apply(lambda x: f"{int(x): ,}h {int((x - int(x)) * 60)}m" if pd.notnull(x) else "-")
    df_market["predicted_points"] = df_market["predicted_points"].apply(lambda x: f"{int(x): ,}" if pd.notnull(x) else "N/A")

    df_market.drop(columns=[ "team_id"], inplace=True)
    pos_mapping = {1: "Torwart", 2: "Abwehr", 3: "Mittelfeld", 4: "Angriff"}
    df_market["player_pos"] = df_market["player_pos"].map(pos_mapping)
    df_market["place_bid_raw"] = 0
    df_market["Place Bid"] = df_market["place_bid_raw"].apply(lambda x: f"{int(x): ,}€".replace(",", ".") if x > 0 else "") 

    df_market.rename(columns={"Playername": "Name", "player_pos": "Position", "team_name": "Team", "player_price": "Price", "expires": "Expires", "predicted_points": "Predicted Points", "points_per_price": "Points / Price", "action": "Action", "next_opponent": "Next Opponents"}, inplace=True)

    st.session_state["market"] = df_market

st.subheader("Transfer Market")

#######################
# Place Bids: 
#######################


edited_market = st.data_editor(
    st.session_state["market"].style.apply(highlight_buy_rows, axis=1), 
    hide_index=True, 
    height="content", 
    disabled=["Name", "Position", "Team", "Price", "Expires", "Predicted Points", "Points / Price", "Action", "Next Opponents"], 
    column_config={"player_id": None, "place_bid_raw": None}, 
    key=f"market_editor_{st.session_state['editor_key']}", 
    on_change=format_bids
)

button_clicked = st.button("Place Bids")

if button_clicked:
    df = st.session_state["market"]
    df_bids = df[df["place_bid_raw"].astype(int) > 0]

    for index, row in df_bids.iterrows():
        Name = row["Name"]
        player_id = row["player_id"]
        bid_price_raw = int(row["place_bid_raw"])
        bid_price = row["Place Bid"]
        price = row["Price"]
        price_raw = int(str(price).replace("€", "").replace(".", ""))
        response = place_bid(player_id, bid_price_raw)
        
        if response.get("status") == "success":
            if bid_price_raw >= price_raw* 1.2 + 300000: # Der Summand kann angepasst werden, je größer der Wert desto höher liegt die Grenze für eine Warnung. 
                st.warning(f"Warning Overpay ({bid_price_raw / price_raw:.2f}x): Successfully placed a bid of {bid_price} for player with Name {Name} and marketvalue {price}.")
            else:
                st.success(f"Successfully placed a bid of {bid_price} for player with Name {Name}.")
        elif bid_price_raw < (price * 0.96):
            st.error(f"Failed to place a bid of {bid_price} for player with Name: {Name}. Reason: The bid is probaly too low")
        else:
            st.error(f"Failed to place a bid of {bid_price} for player with Name: {Name}.")


# hier und/oder in Tab 2 Knopf zum verkaufen von Spielern analog zu Buy, tendenziell eher in Tab 2 
# Budget ergänzen und sofort aktualisieren, wenn etwas unter Place Bid eingetragen wurde
# Remove Bid ergänzen, ggf wenn man auf None setzt ausführen, da None nur wenn man rauslöscht, wird aber aktuell sofort zu "" ersetzt
# refresh button
# Überlegung: damit Gebote dauerhaft gespeichert werden, könnte man statt session_state eine json nutzen
# profit seit letztem Preisupdate ergänzen