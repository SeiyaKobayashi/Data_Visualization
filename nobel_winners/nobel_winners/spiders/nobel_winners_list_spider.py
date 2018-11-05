import scrapy
import re

BASE_URL = 'http://en.wikipedia.org'

# Collection of data I am going to be scraping
class NobelWinnerItem(scrapy.Item):
    name = scrapy.Field()
    link = scrapy.Field()
    year = scrapy.Field()
    category = scrapy.Field()
    country = scrapy.Field()
    gender = scrapy.Field()
    born_in = scrapy.Field()
    date_of_birth = scrapy.Field()
    date_of_death = scrapy.Field()
    place_of_birth = scrapy.Field()
    place_of_death = scrapy.Field()
    text = scrapy.Field()

# Scraping flow: list Page -> individual's Page -> corresponding Wikidata page
class NobelWinnerSpider(scrapy.Spider):
    name = 'nobelwinners_list'
    allowed_domains = ['en.wikipedia.org']
    start_urls = ["https://en.wikipedia.org/wiki/List_of_Nobel_laureates_by_country"]

    # Parse HTTP response using xpath and yield a request
    def parse(self, response):
        filename = response.url.split('/')[-1]
        h2s = response.xpath('//h2')
        # Country list starts from the 3rd element of h2s
        for h2 in h2s[3:]:
            country = h2.xpath('span[@class="mw-headline"]/text()').extract()
            if country:
                winners = h2.xpath('following-sibling::ol[1]')
                for w in winners.xpath('li'):
                    winner_data = process_winner_li(w, country[0])
                    request = scrapy.Request(
                        winner_data['link'],
                        callback=self.parse_bio,
                        dont_filter=True)
                    request.meta['item'] = NobelWinnerItem(**winner_data)
                    yield request

    # Parse individual's wikipedia page (i.e. bio)
    def parse_bio(self, response):
        item = response.meta['item']
        href = response.xpath('//li[@id="t-wikibase"]/a/@href').extract()
        if href:
            request = scrapy.Request(
                href[0],
                callback=self.parse_wikidata,
                dont_filter=True)
            request.meta['item'] = item
            yield request

    # Parse gender, date_of_birth, date_of_death, place_of_birth and place_of_death fields from Wikidata
    def parse_wikidata(self, response):
        item = response.meta['item']
        property_codes = [
            {'name':'gender', 'code':'P21', 'link':True},
            {'name':'date_of_birth','code': 'P569'},
            {'name':'date_of_death','code': 'P570'},
            {'name':'place_of_birth','code': 'P19', 'link':True},
            {'name':'place_of_birth','code': 'P20', 'link':True}
        ]
        p_temp = '//*[@id="{code}"]/div[2]/div[1]/div/div[2]/div/div[1]/div[2]/div[2]/div[1]{link_html}/text()'

        for prop in property_codes:
            link_html = ''
            if prop.get('link'):
                link_html = '/a'
            sel = response.xpath(p_temp.format(code=prop['code'], link_html=link_html))
            if sel:
                item[prop['name']] = sel[0].extract()

        yield item

# Process name, link, year, category, country and born_in fields
def process_winner_li(w, country=None):
    wdata = {}
    wdata['link'] = BASE_URL + w.xpath('a/@href').extract()[0]
    list_text = ' '.join(w.xpath('descendant-or-self::text()').extract())
    wdata['name'] = list_text.split(',')[0].strip()

    year = re.findall('\d{4}', list_text)
    if year:
        wdata['year'] = int(year[0])
    else:
        wdata['year'] = 0
        print('No year in ', list_text)

    category = re.findall(
            'Physics|Chemistry|Physiology or Medicine|Literature|Peace|Economics',
            list_text)
    if category:
        wdata['category'] = category[0]
    else:
        wdata['category'] = ''
        print('No category in ', list_text)

    # Check if one's nationality is different from born-in country
    if country:
        if list_text.find('*') == -1:
            wdata['country'] = country
            wdata['born_in'] = ''
        else:
            wdata['country'] = ''
            wdata['born_in'] = country

    wdata['text'] = list_text
    return wdata
