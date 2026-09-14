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
    # The &headers=1 parameter forces Google to only use the top row as the header
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}&headers=1"
    df = pd.read_csv(url)

    # Prune any phantom columns created by Google Sheets
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    return df

def generate_swiss_pairings(standings_df, matches_df):
    played_pairs = set()
    past_byes = set()
    
    # 1. Map out historical matchups and previous BYEs
    for _, row in matches_df.iterrows():
        p1, p2 = row["Player 1"], row["Player 2"] 
        if p1 == "BYE": past_byes.add(p2)
        elif p2 == "BYE": past_byes.add(p1)
        else:
            played_pairs.add(frozenset([p1, p2]))

    # 2. RANDOM SHUFFLE: Shuffle the dataframe first, then sort by Points 
    shuffled_players = standings_df.sample(frac=1).reset_index(drop=True)
    sorted_players = shuffled_players.sort_values(by="Points", ascending=False, kind="mergesort")["Player"].tolist()
    
    new_matches = []
    unpaired = sorted_players.copy()

    # 3. Handle Odd Player Out (BYE)
    if len(unpaired) % 2 != 0:
        for player in reversed(unpaired):
            if player not in past_byes:
                new_matches.append({"Match Number": "", "Player 1": player, "Player 2": "BYE", "Result": "Player 1 Wins"})
                unpaired.remove(player)
                break

    # 4. Pair remaining players based on closest score
    while unpaired:
        p1 = unpaired.pop(0)
        paired = False
        
        for i, p2 in enumerate(unpaired):
            if frozenset([p1, p2]) not in played_pairs:
                new_matches.append({"Match Number": "", "Player 1": p1, "Player 2": p2, "Result": "Pending"})
                unpaired.pop(i)
                paired = True
                break
                
        if not paired:
            return None 

    return new_matches

# Load the data
tourney_info = load_data("Tournament_Info")
matches = load_data("Match_Structure")
standings = load_data("Standings")
stats = load_data("Lifetime_Stats")

# 2. Global Player Filter
st.markdown("### 🔍 Global Player Search")
player_list = ["All Players"] + sorted(standings["Player"].dropna().unique().tolist())
selected_player = st.selectbox("Select a player to filter the dashboard views:", player_list)

# Filter the public viewing dataframes based on selection
if selected_player != "All Players":
    display_matches = matches[(matches["Player 1"] == selected_player) | (matches["Player 2"] == selected_player)]
    display_standings = standings[standings["Player"] == selected_player]
    display_stats = stats[stats["Player Name"] == selected_player]
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
            # FIX: Fill NaN with blank strings before converting to list
            clean_edited_matches = edited_matches.fillna("")
            updated_data = [clean_edited_matches.columns.values.tolist()] + clean_edited_matches.values.tolist()
            
            secure_payload = {
                "password": st.secrets["admin_password"],
                "data": updated_data
            }
            
            try:
                response = requests.post(st.secrets["web_app_url"], json=secure_payload)
                if response.text == "Success":
                    st.success("Successfully updated the live database!")
                    st.cache_data.clear()
                    st.rerun() 
                else:
                    st.error(f"Failed to update. Google Script Response: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to the database: {e}")
        
        # --- TOURNAMENT CONTROLS ---
        st.divider() 
        st.subheader("Tournament Controls")
        
        if st.button("Generate Next Round"):
            new_pairings = generate_swiss_pairings(standings, matches)
            
            if new_pairings is None:
                st.error("Cannot generate more rounds: All valid combinations have been played!")
            else:
                new_matches_df = pd.DataFrame(new_pairings)
                updated_matches = pd.concat([matches, new_matches_df], ignore_index=True)
                
                # FIX: Fill NaN with blank strings to make JSON compliant
                updated_matches = updated_matches.fillna("")
                
                updated_data = [updated_matches.columns.values.tolist()] + updated_matches.values.tolist()
                
                secure_payload = {
                    "password": st.secrets["admin_password"],
                    "data": updated_data
                }
                
                try:
                    response = requests.post(st.secrets["web_app_url"], json=secure_payload)
                    if response.text == "Success":
                        st.success("Next round generated and pushed to the live database!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Failed to update. Google Script Response: {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to the database: {e}")
        # --------------------------------

    else:
        if entered_password:
            st.error("Incorrect password. Viewing in read-only mode.")
            
        st.dataframe(display_matches, use_container_width=True, hide_index=True)

with tab2:
    st.header("Current Standings")
    st.dataframe(display_standings, use_container_width=True, hide_index=True)

with tab3:
    st.header("Active Tournament Details")
    st.dataframe(tourney_info, use_container_width=True, hide_index=True)

with tab4:
    st.header("Lifetime Player Statistics")
    st.dataframe(display_stats, use_container_width=True, hide_index=True)