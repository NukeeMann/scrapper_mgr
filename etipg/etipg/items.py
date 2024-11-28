# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EtipgPageContent(scrapy.Item):
    # define the fields for your item here like:
    dirpath = scrapy.Field()
    content = scrapy.Field()
    pass

class EtipgFile(scrapy.Item):
    # define the fields for your item here like:
    dirpath = scrapy.Field()
    link = scrapy.Field()
    pass