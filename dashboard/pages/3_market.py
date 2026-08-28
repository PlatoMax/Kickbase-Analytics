import streamlit as st
from components.api import *
from components.tables import *
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
        row_idx = int(id) 
        
        if "Place Bid" in change:
            new_val = change["Place Bid"]
            if new_val and "€" not in str(new_val):
                clean_val = str(new_val).replace(".", "").replace(",", "")
                if clean_val.isdigit():
                    df.loc[row_idx, "Place Bid"] = format_euro(clean_val)
                    df.loc[row_idx, "place_bid_raw"] = int(clean_val)
            elif not new_val:
                df.loc[row_idx, "Place Bid"] = ""
                df.loc[row_idx, "place_bid_raw"] = 0
                
        if "checkbox" in change:
            df.loc[row_idx, "checkbox"] = change["checkbox"]
                
    st.session_state["market"] = df
    
    if current_key in st.session_state:
        del st.session_state[current_key]
    st.session_state["editor_key"] += 1

####################
# DF
####################

st.set_page_config(page_title="Transfer Market", layout="wide")

if "market" not in st.session_state:
    market = fetch_market()
    market_data = market["market"]

    df_market = get_table("market", market_data)    
    st.session_state["market"] = df_market

st.subheader("Transfer Market")

col1, col2 = st.columns([1,2])

with col1:
    st.slider(label="Default Overpay in %", min_value=0, max_value=100, 
          value=10, step=1, key="overpay_slider", width=300)

with col2:
    button_refresh = st.button("Refresh Market")

if button_refresh:
    fetch_market.clear()
    if "market" in st.session_state:
        del st.session_state["market"]
    st.rerun()

#######################
# Place Bids: 
#######################

styled_df = st.session_state["market"].style.apply(lambda row: highlight_rows(row, "buy"), axis=1)

edited_market = st.data_editor(
    styled_df,
    hide_index=True, 
    width="stretch",
    height="content", 
    disabled=["Name", "Position", "Team", "Price", "Expires", "Predicted Points", "Points / Price", "Action", "Next Opponents"], 
    column_config={"player_id": None, "place_bid_raw": None, "team_id": None, "Action": None, "Points / Price": None,
                   "checkbox": st.column_config.CheckboxColumn(
            "Auto-Bid",
            help="Check if you want to buy this player with the selected Overpay percentage",
            default=False,
        )},
                    key=f"market_editor_{st.session_state['editor_key']}", 
                    on_change=format_bids
                    )

button_bids = st.button("Place Bids")

if button_bids:
    df = st.session_state["market"]

    overpay_pct = st.session_state["overpay_slider"]

    df_bids = df_bids = df[(df["checkbox"] == True) | (df["place_bid_raw"].astype(int) > 0)]

    for index, row in df_bids.iterrows():
        Name = row["Name"]
        player_id = row["player_id"]
        price = row["Price"]
        price_raw = int(str(price).replace("€", "").replace(".", ""))

        if row["checkbox"] and int(row["place_bid_raw"]) > 0:
            st.warning(f"⚠️ Warning - {Name}: Manuall bid and selected Overpay are set. Skipped placing a bid for this player.")
            continue

        if row["checkbox"]:
            bid_price_raw = int(price_raw * (1 + overpay_pct / 100))
            bid_price = f"{bid_price_raw:,}€".replace(",", ".")
        else:
            bid_price_raw = int(row["place_bid_raw"])
            bid_price = row["Place Bid"]
        
        response = place_bid(player_id, bid_price_raw)
        
        if response.get("status") == "success":
            if bid_price_raw >= price_raw* 1.2 + 300000: # Der Summand kann angepasst werden, je größer der Wert desto höher liegt die Grenze für eine Warnung. 
                st.warning(f"⚠️ Warning Overpay ({bid_price_raw / price_raw:.2f}x): Successfully placed a bid of {bid_price} for player with Name {Name} and marketvalue {price}.")
            else:
                st.success(f"Successfully placed a bid of {bid_price} for player with Name {Name}.")
        elif bid_price_raw < (price_raw * 0.96):
            st.error(f"Failed to place a bid of {bid_price} for player with Name: {Name}. Reason: The bid is probaly too low")
        else:
            st.error(f"Failed to place a bid of {bid_price} for player with Name: {Name}.")


# Budget ergänzen und sofort aktualisieren, wenn etwas unter Place Bid eingetragen wurde
# 
# Remove Bid ergänzen, ggf wenn man auf None setzt ausführen, da None nur wenn man rauslöscht, wird aber aktuell sofort zu "" ersetzt. Vermutlich dafür speichern der offerID notwendig -> Gebote + offerID in Json speichern
# Überlegung: damit Gebote dauerhaft gespeichert werden, könnte man statt session_state eine json nutzen
# 
# Profit seit letztem Preisupdate ergänzen
# 
# Spalte für Spielerbild und maybe Vereinlogo hinter Vereinsnamen, vermutlich kein Platz
# 
# Neben Prozentualen Overpay auch absoluten Overpay ergänzen
#
# Funktion einfügen, dass man Spieler aus "buy" austragen kann und danach automatisch eine neue Optimierung berechnet wird (maybe erst nach Knopfdruck neu optimieren). 
#   Möglicherweise einfach aus Liste mit Spielern die an Optimizer übergeben wird entfernen und danach wieder hinzufügen mit "hold", sollte dann analog für Tab 2 gehen
#   User warnen das er nun selbständig handel und irgendwo einbauen es rückgängig zu machen -> vermutlich dafür langfristig in Json speichern
#   weitere Option wäre dem Optimizer 0 Punkte als Prognose zu übergeben, in sell (Tab 2) würde dies jedoch nicht gehen
#
# Defaul Overpay maybe runtersetzen, außerdem im session_state speichern
#
# Aktuell habe ich bereits Kane im Kader und der Optimizer will 3 weitere Bayern-Spieler kaufen (Limit erreicht)
# Limit sollte am besten auch nicht hardcodiert sein, sondern aus der API ausgelesen werden.
#
# Mehr Hinweise wenn ein Gebot nicht erfolgreich war, woran es liegen könnte
#
# basierend auf overpay das optimale Team berechnen
#
# optimizer sollte Deadline kennen -> nur Spieler vor der Deadline übergeben
#
# avg. Puntke anzeigen