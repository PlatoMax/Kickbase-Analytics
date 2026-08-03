import requests
import streamlit as st

#----------------------------------------------------------------------------------------------
# Tab 1: Overview
#----------------------------------------------------------------------------------------------

@st.cache_data(ttl=600)
def fetch_kpis():
    response = requests.get("http://127.0.0.1:8000/api/kpi")
    return response.json()

@st.cache_data(ttl=600)
def fetch_leaderboard():
    response = requests.get("http://127.0.0.1:8000/api/leaderboard")
    return response.json()

@st.cache_data(ttl=600)
def fetch_deadline():
    response = requests.get("http://127.0.0.1:8000/api/deadline")
    return response.json()

@st.cache_data(ttl=600)
def fetch_matchups():
    response = requests.get("http://127.0.0.1:8000/api/matchups")
    return response.json()

#----------------------------------------------------------------------------------------------
# Tab 2: Squad
#----------------------------------------------------------------------------------------------

@st.cache_data(ttl=600)
def fetch_optimized_team():
    response = requests.get("http://127.0.0.1:8000/api/optimized_team")
    return response.json()

@st.cache_data(ttl=600)
def fetch_squad():
    response = requests.get("http://127.0.0.1:8000/api/squad")
    return response.json()

#----------------------------------------------------------------------------------------------
# Tab 3: transfer market
#----------------------------------------------------------------------------------------------

@st.cache_data(ttl=600)
def fetch_market():
    response = requests.get("http://127.0.0.1:8000/api/market")
    return response.json()
