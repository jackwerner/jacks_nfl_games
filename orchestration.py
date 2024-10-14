import pandas as pd
from datetime import datetime
from schedule_scrape import get_nfl_schedule
from friendly_scrape import scrape_url_with_timestamp, urls

def standardize_team_names(df, column_name):
    team_name_mapping = {
        'Arizona': 'ARI', 'Atlanta': 'ATL', 'Baltimore': 'BAL', 'Buffalo': 'BUF',
        'Carolina': 'CAR', 'Chicago': 'CHI', 'Cincinnati': 'CIN', 'Cleveland': 'CLE',
        'Dallas': 'DAL', 'Denver': 'DEN', 'Detroit': 'DET', 'Green Bay': 'GB',
        'Houston': 'HOU', 'Indianapolis': 'IND', 'Jacksonville': 'JAX', 'Kansas City': 'KC',
        'LA Chargers': 'LAC', 'LA Rams': 'LAR', 'Las Vegas': 'LV', 'Miami': 'MIA',
        'Minnesota': 'MIN', 'New England': 'NE', 'New Orleans': 'NO', 'NY Giants': 'NYG',
        'NY Jets': 'NYJ', 'Philadelphia': 'PHI', 'Pittsburgh': 'PIT', 'San Francisco': 'SF',
        'Seattle': 'SEA', 'Tampa Bay': 'TB', 'Tennessee': 'TEN', 'Washington': 'WAS'
    }
    df[column_name] = df[column_name].replace(team_name_mapping)
    return df

def get_team_stats():
    all_data = []
    for url in urls:
        df = scrape_url_with_timestamp(url)
        if df is not None:
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, axis=1)
        timestamp_cols = [col for col in combined_df.columns if col.startswith('timestamp')]
        if timestamp_cols:
            combined_df['timestamp'] = combined_df[timestamp_cols[0]]
            combined_df.drop(columns=timestamp_cols[1:], inplace=True)
        combined_df = standardize_team_names(combined_df.reset_index(), 'Team').set_index('Team')
        return combined_df
    else:
        return None

def build_training_dataset(year):
    # Get NFL schedule
    schedule = get_nfl_schedule(year)
    schedule = standardize_team_names(schedule, 'home_team')
    schedule = standardize_team_names(schedule, 'away_team')
    
    # Get team stats
    team_stats = get_team_stats()
    
    if team_stats is None:
        print("Failed to fetch team stats. Exiting.")
        return None
    
    # Prepare home and away team stats
    home_stats = team_stats.add_prefix('home_')
    away_stats = team_stats.add_prefix('away_')
    
    # Merge schedule with team stats
    training_data = schedule.merge(home_stats, left_on='home_team', right_index=True, how='left')
    training_data = training_data.merge(away_stats, left_on='away_team', right_index=True, how='left')
    
    # Calculate point difference (home_score - away_score)
    training_data['point_difference'] = training_data['home_score'] - training_data['away_score']
    
    # Drop rows with missing values
    training_data = training_data.dropna()
    
    return training_data

if __name__ == "__main__":
    year = 2024  # Changed to 2024 as per your example
    training_dataset = build_training_dataset(year)
    
    if training_dataset is not None and not training_dataset.empty:
        # Display the first few rows of the training dataset
        print(training_dataset.head())
        
        # Save the training dataset to a CSV file
        filename = f'datasets/nfl_training_dataset_{year}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        training_dataset.to_csv(filename, index=False)
        print(f"Training dataset for {year} has been saved to '{filename}'")
    else:
        print("Failed to build the training dataset or the dataset is empty.")
        if training_dataset is not None:
            print("DataFrame is empty. Here are the column names:")
            print(training_dataset.columns.tolist())
