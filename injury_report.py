import streamlit as st
import pandas as pd
import requests
from io import StringIO

def get_injury_report():
    # Fetch the latest injury report from the specified URL
    url = "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2024.csv"
    response = requests.get(url)
    injury_data = pd.read_csv(StringIO(response.text))
    
    # Convert date_modified to datetime and sort by most recent first
    injury_data['date_modified'] = pd.to_datetime(injury_data['date_modified'], utc=True)
    injury_data = injury_data.sort_values('date_modified', ascending=False)
    
    # Filter reports from the last 7 days
    last_7_days = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7)
    injury_data = injury_data[injury_data['date_modified'] >= last_7_days]
    
    # Group by team and player, get the most recent report for each player
    latest_injuries = injury_data.groupby(['team', 'full_name']).first().reset_index()
    
    return latest_injuries

def get_depth_charts():
    url = "https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_2024.csv"
    response = requests.get(url)
    depth_charts = pd.read_csv(StringIO(response.text))
    return depth_charts

def display_injury_report():
    st.title("NFL Injury Report")

    injury_data = get_injury_report()
    depth_charts = get_depth_charts()

    # Merge injury data with depth charts
    merged_data = pd.merge(injury_data, depth_charts[['club_code', 'gsis_id', 'full_name', 'depth_team']], 
                           on=['gsis_id','full_name'], how='left')

    # Get unique teams
    teams = sorted(merged_data['team'].unique())

    # Create a selectbox for team selection
    selected_team = st.selectbox("Select a team:", teams)

    # Filter data for the selected team and non-None injuries
    team_injuries = merged_data[(merged_data['club_code'] == selected_team) & 
                                ((merged_data['report_primary_injury'].notna()) | 
                                 (merged_data['report_secondary_injury'].notna()))]

    if team_injuries.empty:
        st.write(f"No injury reports available for {selected_team}")
    else:
        st.subheader(f"Injury Report for {selected_team}")
        
        # Remove duplicates based on 'full_name' and keep the most recent entry
        team_injuries = team_injuries.sort_values('date_modified', ascending=False).drop_duplicates(subset='full_name', keep='first')
        
        # Define position priority
        position_priority = {'QB': 0, 'WR': 1, 'RB': 2, 'CB': 3}
        
        # Create a custom sorting key
        def position_sort_key(pos):
            return position_priority.get(pos, 4)  # Default to 4 for other positions
        
        # Sort by depth_team first, then by position priority
        team_injuries = team_injuries.sort_values(['depth_team', 'position'], 
                                                  key=lambda x: x.map(position_sort_key) if x.name == 'position' else x)

        # Display injury information
        for _, player in team_injuries.iterrows():
            st.write(f"**{player['full_name']}**")
            st.write(f"Position: {player['position']}")
            st.write(f"Depth Team: {player['depth_team']}")
            if pd.notna(player['report_primary_injury']):
                st.write(f"Primary Injury: {player['report_primary_injury']}")
            if pd.notna(player['report_secondary_injury']):
                st.write(f"Secondary Injury: {player['report_secondary_injury']}")
            st.write(f"Status: {player['report_status']}")
            st.write(f"Last Updated: {player['date_modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.write("---")

if __name__ == "__main__":
    display_injury_report()
