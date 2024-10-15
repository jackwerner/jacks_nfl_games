import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from schedule_scrape import get_nfl_schedule
from prediction_input import load_model, get_team_stats, prepare_input_data
from sklearn.preprocessing import StandardScaler
import joblib
from injury_report import display_injury_report, get_injury_counts
import csv
import io

def get_color(injury_count, max_injuries):
    # Create a color gradient from green (0) to red (max_injuries)
    ratio = min(injury_count / max_injuries, 1)  # Ensure ratio doesn't exceed 1
    r = int(255 * ratio)
    g = int(255 * (1 - ratio))
    return f'rgb({r}, {g}, 0)'

def get_upcoming_games(schedule, start_date, end_date):
    # Convert start_date and end_date to datetime64[ns]
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)
    return schedule[(schedule['gameday'] >= start_datetime) & (schedule['gameday'] <= end_datetime)]

def make_prediction(model, scaler, team_stats, home_team, away_team):
    input_data = prepare_input_data(home_team, away_team, team_stats)
    input_data_scaled = scaler.transform(input_data)
    prediction = model.predict(input_data_scaled)[0]
    return prediction

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Game Predictions", "Injury Report"])

    if page == "Game Predictions":
        display_predictions()
    elif page == "Injury Report":
        display_injury_report()

def display_predictions():
    st.title("NFL Game Predictions for the Next 7 Days")

    # Load the model
    print("Loading model...")
    model = load_model('nfl_xgboost_model.json')

    # Load the scaler
    print("Loading scaler...")
    scaler = joblib.load('nfl_standard_scaler.joblib')

    # Get team stats
    print("Fetching team stats...")
    team_stats = get_team_stats()
    if team_stats is None:
        st.error("Failed to fetch team stats. Please try again later.")
        return

    # Remove timestamp columns
    team_stats = team_stats.drop(columns=[col for col in team_stats.columns if col.lower() == 'timestamp'])

    # Get current date and date 7 days from now
    today = datetime.now().date()
    end_date = today + timedelta(days=7)

    # Get NFL schedule for the current year
    current_year = today.year
    schedule = get_nfl_schedule(current_year)

    # Ensure 'gameday' column is datetime64[ns]
    schedule['gameday'] = pd.to_datetime(schedule['gameday'])

    # Filter upcoming games
    upcoming_games = get_upcoming_games(schedule, today, end_date)

    # Get injury counts
    injury_counts = get_injury_counts()

    if upcoming_games.empty:
        st.write("No upcoming games in the next 7 days.")
    else:
        st.write(f"Upcoming games from {today} to {end_date}:")
        
        # Find the maximum number of injuries for color scaling
        max_injuries = max(injury_counts.values()) if injury_counts else 1
        
        # Create a list to store prediction results
        prediction_results = []
        
        for _, game in upcoming_games.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            game_date = game['gameday'].date()
            
            home_injuries = injury_counts.get(home_team, 0)
            away_injuries = injury_counts.get(away_team, 0)
            
            home_color = get_color(home_injuries, max_injuries)
            away_color = get_color(away_injuries, max_injuries)
            
            st.markdown(f"### <span style='color:{away_color}'>{away_team}</span> ({away_injuries} injuries) @ <span style='color:{home_color}'>{home_team}</span> ({home_injuries} injuries) - {game_date}", unsafe_allow_html=True)
            
            try:
                prediction = make_prediction(model, scaler, team_stats, home_team, away_team)
                if prediction > 0:
                    winner = home_team
                    loser = away_team
                    point_difference = prediction
                else:
                    winner = away_team
                    loser = home_team
                    point_difference = -prediction
                
                st.write(f"Prediction: {winner} will defeat {loser} by {point_difference:.2f} points.")
                
                # Add prediction result to the list
                prediction_results.append({
                    'Date': game_date,
                    'Home Team': home_team,
                    'Away Team': away_team,
                    'Predicted Winner': winner,
                    'Predicted Point Difference': abs(point_difference),
                    'Home Team Injuries': home_injuries,
                    'Away Team Injuries': away_injuries
                })
            except KeyError:
                st.write("Unable to make prediction due to missing team data.")
        
        # Create a download button for CSV
        if prediction_results:
            csv_buffer = io.StringIO()
            csv_writer = csv.DictWriter(csv_buffer, fieldnames=prediction_results[0].keys())
            csv_writer.writeheader()
            csv_writer.writerows(prediction_results)
            
            csv_string = csv_buffer.getvalue()
            
            # Get today's date in YYYY-MM-DD format
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            st.download_button(
                label="Download Predictions as CSV",
                data=csv_string,
                file_name=f"nfl_predictions_{today_str}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
