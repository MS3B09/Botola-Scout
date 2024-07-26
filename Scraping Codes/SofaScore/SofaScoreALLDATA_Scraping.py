import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import re
import json
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import urllib3
 
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}
# Disable the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrapeURL(urls):

    all_player_stats = []
    for url in urls:
        print(url)
        # Team ID
        match = re.search(r'/(\d+)$', url)
        team_id = match.group(1)

        res = requests.get(url, headers=headers, verify=False)
        res.raise_for_status()  # Raise an exception for bad status codes

        # The next two lines get around the issue with comments breaking the parsing.
        comm = re.compile("<!--|-->")
        soup = BeautifulSoup(comm.sub("", res.text), 'lxml')

        # Find all <a> tags with href starting with "/player/"
        player_links = soup.find_all('a', href=lambda href: href and href.startswith('/player/'))
        for link in player_links:
            # Name
            name = link.find('div',{"class":"Text cOreSJ"})
            if name is None:
                continue
            else:
                name = name.text.strip()
            print(name)
            # Team
            team = soup.find('h2', {"class":"Text edxjEB"}).text.strip()
            # Team Logo
            logo = 'https://api.sofascore.app/api/v1/team/'+team_id+'/image'
            # Nationality
            nationality = link.find('span',{"class":"Text dJOWjw"})
            if nationality is None:
                nationality = '--'
            else:
                nationality = nationality.text.strip()
            # Player ID
            href = link['href']
            # Regular expression to find the last number in the URL
            match = re.search(r'/(\d+)$', href)
            player_id = match.group(1)
            # Image
            image = 'https://api.sofascore.app/api/v1/player/'+player_id+'/image'
            is_image = check_image_url(image)
            if is_image is False:
                image = 'https://img.a.transfermarkt.technology/portrait/medium/default.jpg'
            player_name = name.lower().replace(' ', '-')
            player_link = 'https://www.sofascore.com/player/'+player_name+'/'+player_id
            age, height, foot, position, shirt_number = scrapeURLplayer(player_link)
            player_stats = extract_player_stats(player_id)

            player_stats['Player'] = name
            player_stats['Player Image'] = image
            player_stats['Team'] = team
            player_stats['Team Logo'] = logo
            player_stats['Nationality'] = nationality
            player_stats['Age']= age
            player_stats['Height'] = height
            player_stats['Preferred Foot'] = foot
            player_stats['Position'] = position
            player_stats['Shirt Number'] = shirt_number

            all_player_stats.append(player_stats)

    df = pd.DataFrame(all_player_stats)
    # Remove 'id', 'type', and 'appearances' from the statistics columns
    df = df.drop(['id', 'type'], axis=1)

    # Define the desired order of columns
    first_columns = ['Player', 'Nationality', 'Team', 'Position', 'Age', 'Height', 'Preferred Foot', 'Shirt Number', 'Player Image', 'Team Logo']
    
    # Get the list of all columns
    all_columns = df.columns.tolist()
    
    # Remove the first_columns from all_columns if they exist
    other_columns = [col for col in all_columns if col not in first_columns]
    
    # Create the new order of columns
    new_order = first_columns + other_columns
    
    # Reorder the DataFrame
    # Note: This will only include columns that actually exist in the DataFrame
    df = df.reindex(columns=[col for col in new_order if col in df.columns])
    return df


def scrapeURLplayer(url):

    res = requests.get(url, headers=headers, verify=False)
    res.raise_for_status()  # Raise an exception for bad status codes

    # The next two lines get around the issue with comments breaking the parsing.
    comm = re.compile("<!--|-->")
    soup = BeautifulSoup(comm.sub("", res.text), 'lxml')
    all_stats = soup.find_all('div', {"class":"Text beCNLk"})
    stats = {
        'age': '--',
        'height': '--',
        'foot': '--',
        'position': '--',
        'shirt_number': '--'
    }
    if len(all_stats) != 0:  
        for stat in all_stats:
            item = stat.text.strip()
            if item.endswith(" yrs"):
                stats['age'] = item
            elif item.endswith(" cm"):
                stats['height'] = item
            elif item in ["Right", "Left", "Both"]:
                stats['foot'] = item
            elif item in ["G", "D", "M", "F"]:
                stats['position'] = item
            elif item.isdigit():
                stats['shirt_number'] = int(item)

    return stats['age'], stats['height'], stats['foot'], stats['position'], stats['shirt_number'] 



def extract_player_stats(player_id):

    api = 'https://www.sofascore.com/api/v1/player/'+player_id+'/unique-tournament/937/season/54108/statistics/overall'
    player_stats = requests.get(api, headers=headers,)
    json_data = player_stats.json()
    try:
        # Parse the JSON string
        #data = json.loads(json_data) if isinstance(json_data, str) else json_data
        # Extract statistics
        statistics = json_data['statistics']
        return statistics
    except (KeyError, IndexError, json.JSONDecodeError):
        # If there's any error in parsing or extracting data, assign '-' to all variables
        with open('default_player_stats.txt', 'r') as f:
            default_stats = json.load(f)
        return default_stats

def check_image_url(url, verify_ssl=True):
    try:
        # Send a GET request to the URL
        response = requests.get(url, headers, verify=verify_ssl, timeout=10)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Check the content type
        content_type = response.headers.get('content-type', '').lower()
        
        if 'image' in content_type:
            # If it's an image, try to open it
            img = Image.open(BytesIO(response.content))
            img.verify()  # Verify that it is, in fact, an image
            return True
        else:
            return False
    
    except (requests.exceptions.SSLError, requests.exceptions.RequestException, 
            UnidentifiedImageError, ValueError, OSError):
        # If SSL verification fails or any other request exception occurs, 
        # retry without SSL verification if it was initially enabled
        if verify_ssl:
            return check_image_url(url, verify_ssl=False)
        return False

def main():
    with open('sofascore_links.txt', 'r') as file:
        urls = file.readlines()
        # Remove newline characters
        urls = [url.strip() for url in urls]

    df_player = scrapeURL(urls)
    df_player.to_csv("BOTOLA Players Stats.csv", encoding='utf-8-sig', index=False)
    print(" SUCCESS !")
    


main()