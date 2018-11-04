from bs4 import BeautifulSoup
import requests
import requests_cache

# Create cache for scraping
requests_cache.install_cache('nodel_pages', backend='sqlite', expire_after=3600)

# Define HEADERS to avoid rejection of requests from Wikipedia
BASE_URL = "https://en.wikipedia.org"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Analyze a web page and covert HTML into soup (i.e. tag tree)
def get_Nobel_soup(url):
    # Get Nobel Laureates page from Wikipedia
    response = requests.get(
        BASE_URL + url,
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

# Get nationality from winner's individual page on Wikipedia
def get_winner_nationality(w):
    soup = get_Nobel_soup(w['link'])
    person_data = {'name': w['name']}
    # Nationality is usually located at the upper-right box tagged 'infobox'
    attr_rows = soup.select('table.infobox tr')
    for tr in attr_rows:
        try:
            attribute = tr.select_one('th').text
            if attribute == 'Nationality':
                person_data[attribute] = tr.select_one('td').text.strip('\n')
        except AttributeError:
            pass
    if not person_data.get('Nationality'):
        person_data['Nationality'] = 'Missing Nationality'

    return person_data

if __name__ == '__main__':
    soup = get_Nobel_soup('/wiki/List_of_Nobel_laureates')
    table = soup.select_one('table.sortable.wikitable')
    winners = get_Nobel_winners(table)
    for w in winners:
        print(get_winner_nationality(w))
