import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Chess Tournament Live", layout="wide")
st.title("🏆 Live Chess Tournament Dashboard")

# Connect to the Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Replace the URL below with the actual link to your Google Sheet
# Ensure your Google Sheet is set to "Anyone with the link can view"
sheet_url = "https://docs.google.com/spreadsheets/d/1wFk8_qx7iHsVnOk_dq93yXn6OcHaODLvmt7E_h06oBM/edit?usp=sharing"

# Read the data from the specific tabs you created
tourney_info = conn.read(spreadsheet=sheet_url, worksheet="Tournament_Info", ttl="5m")
matches = conn.read(spreadsheet=sheet_url, worksheet="Match_Structure", ttl="5m")
stats = conn.read(spreadsheet=sheet_url, worksheet="Lifetime_Stats", ttl="5m")

# Create visual tabs in the web app
tab1, tab2, tab3 = st.tabs(["Live Matches", "Tournament Info", "Player Lifetime Stats"])

with tab1:
    st.header("Current Match Structure")
    st.dataframe(matches, use_container_width=True, hide_index=True)

with tab2:
    st.header("Active Tournament Details")
    st.dataframe(tourney_info, use_container_width=True, hide_index=True)

with tab3:
    st.header("Lifetime Player Statistics")
    st.dataframe(stats, use_container_width=True, hide_index=True)