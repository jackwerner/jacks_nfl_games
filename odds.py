import requests
from lxml import html
import pandas as pd

# URL of the page to scrape
url = "https://www.vegasinsider.com/nfl/odds/las-vegas/"

# Send a GET request to the URL
response = requests.get(url)

# Parse the HTML content
tree = html.fromstring(response.content)

# Use XPath to select the table
table = tree.xpath('//*[@id="full"]/table')[0]

# Extract table headers (only the first set)
headers = ['Number', 'Team'] + [header.text_content().strip() for header in table.xpath('.//th')][:11]
print(f"Number of headers: {len(headers)}")
print("Headers:", headers)

# Extract table rows
rows = []
for row in table.xpath('.//tr')[1:]:  # Skip the header row
    cells = row.xpath('.//td')
    if len(cells) >= 13:
        team_info = cells[0].text_content().strip().split()
        team_number = team_info[0]
        team_name = ' '.join(team_info[1:])
        row_data = [team_number, team_name]
        
        # Separate line from odds for each sportsbook
        for cell in cells[1:12]:
            cell_content = cell.text_content().strip()
            if cell_content:
                if cell_content.startswith(('+', '-')):
                    parts = cell_content.split(None, 1)
                    if len(parts) == 2:
                        line, odds = parts
                    else:
                        line, odds = parts[0], ''
                elif cell_content.lower() == 'n/a':
                    line, odds = 'N/A', ''
                else:
                    line, odds = '', cell_content
                
                # Remove the "     +" string from odds
                odds = odds.replace("     +", "").strip()
                
                # Replace 'even' odds with '100'
                if odds.lower() == 'even':
                    odds = '100'
            else:
                line, odds = '', ''
            row_data.extend([line.strip(), odds.strip()])
        
        rows.append(row_data)

print(f"Number of rows: {len(rows)}")
print(f"Number of columns in first row: {len(rows[0])}")
print("First few rows:", rows[:5])

# Update headers to reflect separated line and odds
new_headers = ['Number', 'Team']
for header in headers[2:]:
    new_headers.extend([f"{header} Line", f"{header} Odds"])

# Create a pandas DataFrame
df = pd.DataFrame(rows, columns=new_headers)

# Display the first few rows of the DataFrame
print(df.head())

# Optionally, save the DataFrame to a CSV file
df.to_csv('nfl_odds.csv', index=False)
print("Data saved to nfl_odds.csv")

# Add this team name mapping dictionary
team_name_mapping = {
    'Cardinals': 'ARI', 'Falcons': 'ATL', 'Ravens': 'BAL', 'Bills': 'BUF',
    'Panthers': 'CAR', 'Bears': 'CHI', 'Bengals': 'CIN', 'Browns': 'CLE',
    'Cowboys': 'DAL', 'Broncos': 'DEN', 'Lions': 'DET', 'Packers': 'GB',
    'Texans': 'HOU', 'Colts': 'IND', 'Jaguars': 'JAX', 'Chiefs': 'KC',
    'Raiders': 'LV', 'Chargers': 'LAC', 'Rams': 'LAR', 'Dolphins': 'MIA',
    'Vikings': 'MIN', 'Patriots': 'NE', 'Saints': 'NO', 'Giants': 'NYG',
    'Jets': 'NYJ', 'Eagles': 'PHI', 'Steelers': 'PIT', '49ers': 'SF',
    'Seahawks': 'SEA', 'Buccaneers': 'TB', 'Titans': 'TEN', 'Commanders': 'WAS'
}

# Function to get odds for a specific team
def get_odds_for_team(team_code):
    team_name = next((name for name, code in team_name_mapping.items() if code == team_code), None)
    if team_name:
        team_row = df[df['Team'] == team_name]
        if not team_row.empty:
            return team_row.iloc[0]['DraftKings Odds'], team_row.iloc[0]['DraftKings Line']
    return None, None
