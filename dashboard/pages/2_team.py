import streamlit as st
from components.api import *

st.set_page_config(page_title="My Team", layout="wide")


optimized_team = fetch_optimized_team()
squad = fetch_squad()

st.write(optimized_team)
st.write(squad)