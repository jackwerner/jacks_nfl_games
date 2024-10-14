import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from friendly_scrape import scrape_url_with_timestamp, urls
from orchestration import standardize_team_names

def load_model(model_path):
    model = XGBRegressor()
    model.load_model(model_path)
    return model

def get_team_stats():
    all_data = []
    for url in urls:
        df = scrape_url_with_timestamp(url)
        if df is not None:
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, axis=1)
        timestamp_cols = [col for col in combined_df.columns if col.startswith('timestamp')]
        print(combined_df.columns)
        if timestamp_cols:
            combined_df['timestamp'] = combined_df[timestamp_cols[0]]
            combined_df.drop(columns=timestamp_cols[1:], inplace=True)
        combined_df = standardize_team_names(combined_df.reset_index(), 'Team').set_index('Team')
        return combined_df
    else:
        return None

def prepare_input_data(home_team, away_team, team_stats):
    home_stats = team_stats.loc[home_team].add_prefix('home_')
    away_stats = team_stats.loc[away_team].add_prefix('away_')
    input_data = pd.concat([home_stats, away_stats])
    return input_data.to_frame().T

def main():
    # Load the model
    model = load_model('nfl_xgboost_model.json')

    # Get team stats
    team_stats = get_team_stats()
    if team_stats is None:
        print("Failed to fetch team stats. Exiting.")
        return

    # Remove timestamp columns
    team_stats = team_stats.drop(columns=[col for col in team_stats.columns if col.lower() == 'timestamp'])

    # Get user input for home and away teams
    home_team = input("Enter the home team (e.g., DAL for Dallas): ").upper()
    away_team = input("Enter the away team (e.g., NYG for NY Giants): ").upper()

    # Prepare input data
    input_data = prepare_input_data(home_team, away_team, team_stats)

    # Scale the input data
    scaler = StandardScaler()
    input_data_scaled = scaler.fit_transform(input_data)

    # Make prediction
    prediction = model.predict(input_data_scaled)[0]

    # Interpret the prediction
    if prediction > 0:
        winner = home_team
        loser = away_team
        point_difference = prediction
    else:
        winner = away_team
        loser = home_team
        point_difference = -prediction

    print(f"\nPrediction: {winner} will defeat {loser} by {point_difference:.2f} points.")

if __name__ == "__main__":
    main()
