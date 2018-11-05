import scrapy
import re

class NobelWinnerItem(scrapy.Item):
    country = scrapy.Field()
    name = scrapy.Field()
    link_text = scrapy.Field()

class NobelWinnerSpider(scrapy.Spider):
    name = 'nobelwinners_list'
    allowed_domains = ['en.wikipedia.org']
    start_urls = ["https://en.wikipedia.org/wiki/List_of_Nobel_laureates_by_country"]

    # Parse HTTP response using xpath
    def parse(self, response):
        h2s = response.xpath('//h2')
        # Country list starts from the 3rd element of h2s
        for h2 in h2s[3:]:
            country = h2.xpath('span[@class="mw-headline"]/text()').extract()
            if country:
                winners = h2.xpath('following-sibling::ol[1]')
                for w in winners.xpath('li'):
                    list_text = w.xpath('descendant-or-self::text()').extract()
                    yield NobelWinnerItem(
                        country=country[0],
                        name=list_text[0],
                        link_text=''.join(list_text)
                        )
