from bs4 import BeautifulSoup
import requests

# Define HEADERS to avoid rejection of requests from Wikipedia
BASE_URL = "https://en.wikipedia.org"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Analyze a web page and covert HTML into soup (i.e. tag tree)
def get_Nobel_soup():
    # Get Nobel Laureates page from Wikipedia
    response = requests.get(
        BASE_URL + '/wiki/List_of_Nobel_laureates',
        headers=HEADERS)
    # Return soup
    return BeautifulSoup(response.content, "lxml")

# Get a list of types of Nobel Prize (e.g. Physics, Literature)
def get_Nobel_titles(table):
    titles = []
    # Get each category from 'th' tag which is in 'tr' tag (but ignore the first 'Year' column)
    for th in table.select_one('tr').select('th')[1:]:
        # If it contains a link, store its title and href
        # e.g. {title: Physics, href: https://en.wikipedia.org/wiki/List_of_Nobel_laureates_in_Physics}
        link = th.select_one('a')
        if link:
            titles.append({'title':link.text,\
                         'href':link.attrs['href']})
        else:
            titles.append({'title':th.text, 'href':None})
    return titles

# Get a list of Nobel Laureates
def get_Nobel_winners(table):
    titles = get_Nobel_titles(table)
    winners = []
    # Iterate through each year and each winner
    for row in table.select('tr')[1:-1]:
        # If year contains a link, get only the first four characters (e.g. 2016)
        if row.select_one('td').select_one('a'):
            year = int(row.select_one('td').text[0:4])
        else:
            year = int(row.select_one('td').text)

        for i, td in enumerate(row.select('td')[1:]):
            for winner in td.select('a'):
                href_winner = winner.attrs['href']
                if not href_winner.startswith('#endnote'):
                    winners.append({
                        'year':year,
                        'category':titles[i]['title'],
                        'name':winner.text,
                        'link':winner.attrs['href']
                    })
    return winners

if __name__ == '__main__':
    soup = get_Nobel_soup()
    table = soup.select_one('table.sortable.wikitable')
    print(get_Nobel_winners(table))
