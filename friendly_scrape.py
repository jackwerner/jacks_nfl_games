import requests
from lxml import html
import pandas as pd
import time
from datetime import datetime

# URLs of the webpages
urls = [
    "https://www.teamrankings.com/nfl/stat/opponent-offensive-touchdowns-per-game",
    "https://www.teamrankings.com/nfl/stat/offensive-touchdowns-per-game",
    "https://www.teamrankings.com/nfl/stat/points-per-game",
    "https://www.teamrankings.com/nfl/stat/opponent-points-per-game",
    "https://www.teamrankings.com/nfl/stat/yards-per-game",
    "https://www.teamrankings.com/nfl/stat/opponent-yards-per-game",
    "https://www.teamrankings.com/nfl/stat/passing-yards-per-game",
    "https://www.teamrankings.com/nfl/stat/rushing-yards-per-game",
    "https://www.teamrankings.com/nfl/stat/turnover-margin-per-game",
    "https://www.teamrankings.com/nfl/stat/average-time-of-possession-net-of-ot",
    "https://www.teamrankings.com/nfl/stat/opponent-passing-yards-per-game",
    "https://www.teamrankings.com/nfl/stat/opponent-rushing-yards-per-game"
]

# Function to extract data from a table
def extract_table_data(table):
    headers = [header.text_content().strip() for header in table.xpath('.//th')]
    rows = [[cell.text_content().strip() for cell in row.xpath('.//td')] for row in table.xpath('.//tr')]
    # Filter out rows where all cells are empty or None
    rows = [row for row in rows if any(cell for cell in row)]
    return headers, rows

# Function to scrape data from a URL
def scrape_url(url):
    response = requests.get(url)
    tree = html.fromstring(response.content)
    
    # XPath for the table
    table_xpath = '//table'
    
    # Try to find the table
    tables = tree.xpath(table_xpath)
    
    if not tables:
        print(f"Table not found for {url}. Trying alternative methods...")
        
        # Method 1: Wait and retry (in case of dynamic content)
        time.sleep(5)
        response = requests.get(url)
        tree = html.fromstring(response.content)
        tables = tree.xpath(table_xpath)
    
    if tables:
        table = tables[0]
        headers, rows = extract_table_data(table)
        
        # Create a DataFrame with the data
        df = pd.DataFrame(rows, columns=headers)
        
        # Remove rows where all columns are None or empty
        df = df.dropna(how='all')
        
        return df
    else:
        print(f"Table not found for {url}. Here's what the page contains:")
        print(tree.xpath('//body')[0].text_content())
        return None

def scrape_url_with_timestamp(url):
    df = scrape_url(url)
    if df is not None:
        df['timestamp'] = datetime.now().isoformat()
        stat_name = url.split('/')[-1].replace('-', '_')
        df.set_index('Team', inplace=True)
        df.rename(columns={'2024': stat_name}, inplace=True)
        
        # Format time of possession as minutes
        if 'time_of_possession' in stat_name:
            df[stat_name] = df[stat_name].apply(lambda x: sum(float(i) * 60 ** index for index, i in enumerate(reversed(x.split(':')))) / 60)
        
        # Format turnover margin as float
        if 'turnover_margin' in stat_name:
            df[stat_name] = df[stat_name].apply(lambda x: float(x))
        
        df = df[[stat_name, 'timestamp']]
    return df

# Scrape data from all URLs
all_data = []
for i, url in enumerate(urls, 1):
    df = scrape_url_with_timestamp(url)
    
    if df is not None:
        print(f"\nFetching data from URL {i}")
        # print(df)
        all_data.append(df)
    else:
        print(f"Failed to scrape data from URL {i}")

# Combine all dataframes
if all_data:
    combined_df = pd.concat(all_data, axis=1)
    
    # Remove duplicate timestamp columns
    timestamp_cols = [col for col in combined_df.columns if col.startswith('timestamp')]
    if timestamp_cols:
        combined_df['timestamp'] = combined_df[timestamp_cols[0]]
        combined_df.drop(columns=timestamp_cols[1:], inplace=True)
    
    # Save combined data to CSV
    combined_filename = f'datasets/nfl_combined_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    combined_df.to_csv(combined_filename)
    print(f"Combined data saved to {combined_filename}")
    print("\nCombined Dataset:")
    print(combined_df)
else:
    print("No data was successfully scraped.")
