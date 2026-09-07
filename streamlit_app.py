import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Chessers Chess Tournament", layout="wide")
st.title("🏆 Chessers Chess Tournament Dashboard")

# Your exact Google Sheet ID
sheet_id = "1wFk8_qx7iHsVnOk_dq93yXn6OcHaODLvmt7E_h06oBM"

# Function to safely download public tabs as CSVs by exact sheet name
@st.cache_data(ttl=300)
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    
    # Prune any phantom columns created by Google Sheets
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    return df

# Load specific tabs explicitly by their Google Sheet tab names
tourney_info = load_data("Tournament_Info")
matches = load_data("Match_Structure")
standings = load_data("Standings")
stats = load_data("Lifetime_Stats")

# Create visual tabs
tab1, tab2, tab3, tab4 = st.tabs(["Live Matches", "Standings", "Tournament Info", "Player Lifetime Stats"])

with tab1:
    st.header("Current Match Structure")
    
    # Password input box
    entered_password = st.text_input("Enter Admin Password to Edit Results", type="password")
    
    # Validate password
    if entered_password == st.secrets["admin_password"]:
        st.success("Admin access granted!")
        st.write("Edit the 'Result' column below and click Save.")
        
        # Display editable table
        edited_matches = st.data_editor(matches, use_container_width=True, hide_index=True)
        
        if st.button("Save Match Results"):
            # Prepare the raw data
            updated_data = [edited_matches.columns.values.tolist()] + edited_matches.values.tolist()
            
            # Package the data AND the password together
            secure_payload = {
                "password": st.secrets["admin_password"],
                "data": updated_data
            }
            
            # Pull the protected URL from secrets
            web_app_url = st.secrets["web_app_url"]
            
            try:
                # Send the secure package to Google
                response = requests.post(web_app_url, json=secure_payload)
                
                if response.text == "Success":
                    st.success("Successfully updated the live database!")
                    st.cache_data.clear()
                else:
                    st.error(f"Failed to update. Google Script Response: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to the database: {e}")
                
    else:
        if entered_password:
            st.error("Incorrect password. Viewing in read-only mode.")
            
        # Display read-only table for participants
        st.dataframe(matches, use_container_width=True, hide_index=True)

with tab2:
    st.header("Current Standings")
    st.dataframe(standings, use_container_width=True, hide_index=True)

with tab3:
    st.header("Active Tournament Details")
    st.dataframe(tourney_info, use_container_width=True, hide_index=True)

with tab4:
    st.header("Lifetime Player Statistics")
    st.dataframe(stats, use_container_width=True, hide_index=True)