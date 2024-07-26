import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import re
import urllib3
 
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}
# Disable the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrapeURL(urls):

    pre_df_player = dict()
    features = ['Player', 'Team', 'Position','Market Value']

    for url in urls:
        print(url)
        res = requests.get(url, headers=headers, verify=False)
        res.raise_for_status()  # Raise an exception for bad status codes


        # The next two lines get around the issue with comments breaking the parsing.
        comm = re.compile("<!--|-->")
        soup = BeautifulSoup(comm.sub("", res.text), 'lxml')

        # Team
        team = soup.find("h1", {"class":"data-header__headline-wrapper data-header__headline-wrapper--oswald"}).text.strip()
    
        table = soup.find_all("table", class_="items")
        player_table = table[0]

        rows_player = player_table.find_all('tr', class_=['odd', 'even'])

        for row in rows_player:
            # Name
            cell_name = row.find('td', class_="hauptlink")
            name = cell_name.find('a').text.strip()
            # Market Value
            try:
                cell_mv = row.find('td', class_="rechts hauptlink")
                mv = cell_mv.find('a').text.strip()
            except AttributeError:
                mv = '-'

            cells_td = row.find_all('td')
            # Pos
            cell_pos = cells_td[4]
            pos = cell_pos.text.strip()
 
            values = [name, team, pos, mv]
            i = 0
            for feature in features:
                if feature in pre_df_player:
                    pre_df_player[feature].append(values[i])
                else:
                    pre_df_player[feature] = [values[i]]
                i += 1


    df_player = pd.DataFrame.from_dict(pre_df_player)
    return df_player
   

def main():
    with open('transfermarket_links.txt', 'r') as file:
        urls = file.readlines()
        # Remove newline characters
        urls = [url.strip() for url in urls]

    df_player = scrapeURL(urls)
    df_player.to_csv("Botola Players MVs.csv", encoding='utf-8-sig', index=False)
    print(" SUCCESS !")

main()