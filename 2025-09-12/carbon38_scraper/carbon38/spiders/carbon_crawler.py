import scrapy
from urllib.parse import urljoin
from carbon38.items import ProductUrlItem

class ProductUrlsSpider(scrapy.Spider):
    name = 'product_urls'
    allowed_domains = ['carbon38.com']
    start_urls = [
        'https://carbon38.com/en-in/collections/tops?filter.p.m.custom.available_or_waitlist=1'
    ]

    def parse(self, response):

        # Example XPath: you might adjust based on HTML structure:
        product_link_xpath = "//a[@class='ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage']/@href"

        urls = response.xpath(product_link_xpath).getall()
        if not urls:
            self.logger.warning(f"No product URLs found on {response.url}") 

        for rel in urls:
            prod_url = urljoin(response.url, rel.strip())
            item = ProductUrlItem()
            item['url'] = prod_url
            yield item

        # Pagination: check for “next page” link
        next_page_xpath = "//a[@class='Pagination__NavItem Link Link--primary' and @title='Next page']/@href"
        next_page = response.xpath(next_page_xpath).get()
        if next_page:
            next_page_url = urljoin(response.url, next_page.strip())
            yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.logger.info(f"No next page found on {response.url}")
            if next_page:
                next_page_url = urljoin(response.url, next_page.strip())
                yield scrapy.Request(next_page_url, callback=self.parse)
