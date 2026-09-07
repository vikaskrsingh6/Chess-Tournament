import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Chessers Chess Tournament", layout="wide")
st.title("🏆 Chessers Chess Tournament Dashboard")

# Your exact Google Sheet ID from your URL
sheet_id = "1wFk8_qx7iHsVnOk_dq93yXn6OcHaODLvmt7E_h06oBM"

# This function safely downloads the public tabs as CSVs directly
@st.cache_data(ttl=300) # Caches data for 5 minutes to keep your app fast
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    
    # Prune any phantom columns created by Google Sheets
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    return df

# Load your specific tabs
tourney_info = load_data("Tournament_Info")
matches = load_data("Match_Structure")
stats = load_data("Lifetime_Stats")

# Create visual tabs in the web app
tab1, tab2, tab3 = st.tabs(["Live Matches", "Tournament Info", "Player Lifetime Stats"])

with tab1:
    st.header("Current Match Structure")
    st.write("Edit the 'Result' column below and click Save to push updates to the database.")
    
    # Change st.dataframe to st.data_editor to make the table interactive
    edited_matches = st.data_editor(matches, use_container_width=True, hide_index=True)
    
    if st.button("Save Match Results"):
        # Convert the edited table back into a raw format for Google Sheets
        updated_data = [edited_matches.columns.values.tolist()] + edited_matches.values.tolist()
        
        # Send the data to your Apps Script URL
        # IMPORTANT: Replace the placeholder below with your actual deployed URL
        web_app_url = "https://script.google.com/macros/s/AKfycbzzbf-OzXtCAGH6ihZBPiIMQriWQJWYMITIDMW-Ry5FYwvA3FHSVF-ZFfntcE-wz2k/exec"
        
        try:
            response = requests.post(web_app_url, json=updated_data)
            
            if response.text == "Success":
                st.success("Successfully updated the live database!")
                st.cache_data.clear() # Forces Streamlit to instantly download the fresh data
            else:
                st.error(f"Failed to update. Google Script Response: {response.text}")
        except Exception as e:
            st.error(f"Failed to connect to the database: {e}")

with tab2:
    st.header("Active Tournament Details")
    st.dataframe(tourney_info, use_container_width=True, hide_index=True)

with tab3:
    st.header("Lifetime Player Statistics")
    st.dataframe(stats, use_container_width=True, hide_index=True)