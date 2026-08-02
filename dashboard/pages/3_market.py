import streamlit as st
from components.api import *

st.set_page_config(page_title="Transfer Market", layout="wide")

market = fetch_market()
st.write(market)
