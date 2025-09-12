# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class ProductUrlItem(scrapy.Item):
    url = scrapy.Field()

class Carbon38ScraperItem(scrapy.Item):
    primary_image_url = scrapy.Field()
    brand = scrapy.Field()
    product_name = scrapy.Field()
    price = scrapy.Field()
    colour = scrapy.Field()
    sizes = scrapy.Field()
    sku = scrapy.Field()
    description = scrapy.Field()
    reviews = scrapy.Field()
    product_id = scrapy.Field()
    product_url = scrapy.Field()
    image_urls = scrapy.Field()
