import scrapy
import re

BASE_URL = 'http://en.wikipedia.org'

# Collection of data I am going to be scraping
class NobelWinnerItemBio(scrapy.Item):
    name = scrapy.Field()
    link = scrapy.Field()
    mini_bio = scrapy.Field()
    image_urls = scrapy.Field()
    bio_image = scrapy.Field()
    images = scrapy.Field()

class NobelWinnerSpiderBio(scrapy.Spider):
    name = 'nobelwinners_minibio'
    allowed_domains = ['en.wikipedia.org']
    start_urls = ["https://en.wikipedia.org/wiki/List_of_Nobel_laureates_by_country"]
    custom_settings = {'ITEM_PIPELINES': {'nobel_winners.pipelines.NobelImagesPipeline':1}}

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
                    winner_data = {}
                    winner_data['link'] = BASE_URL + w.xpath('a/@href').extract()[0]
                    list_text = ' '.join(w.xpath('descendant-or-self::text()').extract())
                    winner_data['name'] = list_text.split(',')[0].strip()
                    request = scrapy.Request(
                        winner_data['link'],
                        callback=self.parse_mini_bio,
                        dont_filter=True)
                    request.meta['item'] = NobelWinnerItemBio(**winner_data)
                    yield request

    # Parse image_urls and mini_bio fields
    def parse_mini_bio(self, response):
        BASE_URL_ESCAPED = 'http:\/\/en.wikipedia.org'
        item = response.meta['item']
        
        item['image_urls'] = []
        img_src = response.xpath('//table[contains(@class, "infobox")]//img/@src')
        if img_src:
            item['image_urls'] = ['http:' + img_src[0].extract()]

        mini_bio = ''
        # Snippet's XPath is lacated either at ...p[1] or ...p[2]
        brf_para = response.xpath('//*[@id="mw-content-text"]/div/p[1][text() or normalize-space(.)=""]').extract()
        if brf_para[0] == '<p class=\"mw-empty-elt\">\n\n</p>':
            brf_para = response.xpath('//*[@id="mw-content-text"]/div/p[2][text() or normalize-space(.)=""]').extract()
        for p in brf_para:
            if p == '<p></p>':     # Check if it's the end of paragraph
                break
            mini_bio += p

        mini_bio = mini_bio.replace('href="/wiki', 'href="' + BASE_URL + '/wiki')
        mini_bio = mini_bio.replace('href="#', item['link'] + '#')
        item['mini_bio'] = mini_bio

        yield item
