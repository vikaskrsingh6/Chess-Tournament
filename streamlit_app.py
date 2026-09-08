import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="The Chessers", layout="wide")

# 1. Display the Custom Banner
st.image("Banner.png", use_container_width=True)

st.title("🏆 The Chessers Tournament Dashboard")

sheet_id = "1wFk8_qx7iHsVnOk_dq93yXn6OcHaODLvmt7E_h06oBM"

@st.cache_data(ttl=300)
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

tourney_info = load_data("Tournament_Info")
matches = load_data("Match_Structure")
standings = load_data("Standings")
stats = load_data("Lifetime_Stats")

# 2. Global Player Filter
st.markdown("### 🔍 Global Player Search")
# Extract a clean list of all unique players from the standings
player_list = ["All Players"] + sorted(standings["Player"].dropna().unique().tolist())
selected_player = st.selectbox("Select a player to filter the dashboard views:", player_list)

# Filter the public viewing dataframes based on selection
if selected_player != "All Players":
    display_matches = matches[(matches["Player_1"] == selected_player) | (matches["Player_2"] == selected_player)]
    display_standings = standings[standings["Player"] == selected_player]
    display_stats = stats[stats["Player"] == selected_player]
else:
    display_matches = matches
    display_standings = standings
    display_stats = stats

tab1, tab2, tab3, tab4 = st.tabs(["Live Matches", "Standings", "Tournament Info", "Player Lifetime Stats"])

with tab1:
    st.header("Current Match Structure")
    
    entered_password = st.text_input("Enter Admin Password to Edit Results", type="password")
    
    if entered_password == st.secrets["admin_password"]:
        st.success("Admin access granted!")
        st.warning("Admin Mode: Displaying the complete match list to ensure safe database saving.")
        
        # 3. Data Integrity Dropdown
        edited_matches = st.data_editor(
            matches, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Result": st.column_config.SelectboxColumn(
                    "Result",
                    help="Select the exact match outcome",
                    options=["Player 1 Wins", "Player 2 Wins", "Pending"],
                    required=True
                )
            }
        )
        
        if st.button("Save Match Results"):
            updated_data = [edited_matches.columns.values.tolist()] + edited_matches.values.tolist()
            
            secure_payload = {
                "password": st.secrets["admin_password"],
                "data": updated_data
            }
            web_app_url = st.secrets["web_app_url"]
            
            try:
                response = requests.post(web_app_url, json=secure_payload)
                if response.text == "Success":
                    st.success("Successfully updated the live database!")
                    st.cache_data.clear()
                    st.rerun() 
                else:
                    st.error(f"Failed to update. Google Script Response: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to the database: {e}")
                
    else:
        if entered_password:
            st.error("Incorrect password. Viewing in read-only mode.")
            
        # Display the publicly filtered read-only table
        st.dataframe(display_matches, use_container_width=True, hide_index=True)

with tab2:
    st.header("Current Standings")
    st.dataframe(display_standings, use_container_width=True, hide_index=True)

with tab3:
    st.header("Active Tournament Details")
    st.dataframe(tourney_info, use_container_width=True, hide_index=True) # Usually doesn't need filtering

with tab4:
    st.header("Lifetime Player Statistics")
    st.dataframe(display_stats, use_container_width=True, hide_index=True)