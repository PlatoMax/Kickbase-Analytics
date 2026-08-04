import streamlit as st
from components.api import *
import pandas as pd

####################
# DF
####################
def highlight_buy_rows(row):
    if row['Action'] == 'buy':
        return ['background-color: rgba(46, 204, 113, 0.3)'] * len(row)
    else:
        return [''] * len(row)

st.set_page_config(page_title="Transfer Market", layout="wide")

market = fetch_market()
df_market = pd.DataFrame(market["market"])

df_market["player_price"] = df_market["player_price"].apply(lambda x: f"{int(x): ,}€".replace(",", "."))
df_market.sort_values(by=["expires"], inplace=True)
df_market["expires"] = df_market["expires"].apply(lambda x: f"{int(x): ,}h {int((x - int(x)) * 60)}m" if pd.notnull(x) else "-")
df_market["predicted_points"] = df_market["predicted_points"].apply(lambda x: f"{int(x): ,}" if pd.notnull(x) else "N/A")

df_market.drop(columns=[ "team_id"], inplace=True)
pos_mapping = {1: "Torwart", 2: "Abwehr", 3: "Mittelfeld", 4: "Angriff"}
df_market["player_pos"] = df_market["player_pos"].map(pos_mapping)
df_market["Place Bid"] = 0

df_market.rename(columns={"Playername": "Name", "player_pos": "Position", "team_name": "Team", "player_price": "Price", "expires": "Expires", "predicted_points": "Predicted Points", "points_per_price": "Points / Price", "action": "Action", "next_opponent": "Next Opponents"}, inplace=True)

styled_market = df_market.style.apply(highlight_buy_rows, axis=1)
st.subheader("Transfer Market")



#######################
# Place Bids: 
#######################
   

edited_market = st.data_editor(styled_market, hide_index=True, height="content", 
                               disabled=["Name", "Position", "Team", "Price", "Expires", 
                                         "Predicted Points", "Points / Price", "Action", "Next Opponents"], column_config={"player_id": None})

button_clicked = st.button("Place Bids")

if button_clicked:
    df_bids = edited_market[edited_market["Place Bid"].astype(int) > 0]
    df_bids = df_bids[["Name", "player_id", "Price", "Place Bid"]]
    df_bids["Price"] =df_bids["Price"].str.replace("€", "").str.replace(".", "").astype(int)
    for index, row in df_bids.iterrows():
        Name = row["Name"]
        player_id = row["player_id"]
        bid_price = row["Place Bid"]
        price = row["Price"]
        response = place_bid(player_id, bid_price)
        if response.get("status") == "success":
            st.success(f"Successfully placed a bid of {bid_price}€ for player with Name {Name}.")
        elif bid_price < (price * 0.90):
            st.error(f"Failed to place a bid of {bid_price}€ for player with Name: {Name}. Reason: The bid is probaly too low")
        else:
            st.error(f"Failed to place a bid of {bid_price}€ for player with Name: {Name}.")

# hier und/oder in Tab 2 Knopf zum verkaufen von Spielern analog zu Buy