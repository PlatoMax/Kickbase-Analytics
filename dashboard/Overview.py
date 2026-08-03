import streamlit as st
import pandas as pd
from components.api import *
from datetime import datetime

st.set_page_config(page_title="Dashboard", layout="wide")

kpi_data = fetch_kpis()
leaderboard_dict = fetch_leaderboard()
deadline_data = fetch_deadline()
matchups = fetch_matchups()

col1, col2 = st.columns([1,2])

with col1:
    with st.container(border=True):
        st.subheader("KPI Overview")
        st.metric(label="Matchday", value=f"{deadline_data['matchday']}")

        deadline_string = deadline_data["deadline"].replace("Z", "+00:00") 
        deadline_date = datetime.fromisoformat(deadline_string)
        st.metric(label="Deadline", value= deadline_date.strftime("%d.%m.%y %H:%M") + "Uhr")

        st.metric(label="Budget", value=f"{kpi_data['budget']} €")
        st.metric(label="Expected Points", value=kpi_data['expected_points'])

    df = pd.DataFrame(leaderboard_dict["leaderboard"], columns=["Manager", "Punkte"])
    df.index = range(1, len(df) + 1)
    df.index.name = "Platz"
    st.dataframe(df)