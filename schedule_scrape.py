import nfl_data_py as nfl
import pandas as pd

def get_nfl_schedule(year):
    # Fetch the NFL schedule for the specified year
    schedule = nfl.import_schedules([year])
    
    # Select relevant columns
    columns = ['game_id', 'season', 'week', 'gameday', 'gametime', 'home_team', 'away_team', 'home_score', 'away_score']
    schedule = schedule[columns]
    
    # Convert gameday to datetime
    schedule['gameday'] = pd.to_datetime(schedule['gameday'])
    
    return schedule

if __name__ == "__main__":
    # Example usage
    year = 2024  # You can change this to the desired year
    nfl_schedule = get_nfl_schedule(year)
    
    # Display the first few rows of the schedule
    print(nfl_schedule.head())
    
    # Optionally, save the schedule to a CSV file
    # nfl_schedule.to_csv(f'nfl_schedule_{year}.csv', index=False)
    # print(f"Schedule for {year} has been saved to 'nfl_schedule_{year}.csv'")

