import streamlit as st
import pandas as pd
from components.api import *

st.set_page_config(page_title="Dashboard", layout="wide")

kpi_data = fetch_kpis()
leaderboard = fetch_leaderboard()
deadline = fetch_deadline()


st.write(kpi_data)
st.write(leaderboard)
st.write(deadline)