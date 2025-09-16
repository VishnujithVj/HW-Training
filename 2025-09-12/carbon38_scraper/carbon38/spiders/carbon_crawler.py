import scrapy
import time
import psutil
import logging
from urllib.parse import urljoin
from carbon38.items import ProductUrlItem


class ProductUrlsSpider(scrapy.Spider):
    name = "product_urls"
    allowed_domains = ["carbon38.com"]
    start_urls = [
        "https://carbon38.com/en-in/collections/tops?filter.p.m.custom.available_or_waitlist=1"
    ]

    def __init__(self, *args, **kwargs):
        super(ProductUrlsSpider, self).__init__(*args, **kwargs)
        # logging setup
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.start_time = time.time()

    def parse(self, response):
        """Parse product URLs from a collection page and follow pagination."""

        self.logger.info(f"Response: {response.status} | {response.url}")

        product_link_xpath = (
            "//a[@class='ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage']/@href"
        )

        product_links = response.xpath(product_link_xpath).getall()

        if not product_links:
            self.logger.warning(f"No product URLs found on {response.url}")

        for relative_link in product_links:
            absolute_url = urljoin(response.url, relative_link.strip())
            item = ProductUrlItem()
            item["url"] = absolute_url
            yield item

        # Handle pagination
        next_page_xpath = (
            "//a[@class='Pagination__NavItem Link Link--primary' and @title='Next page']/@href"
        )
        next_page = response.xpath(next_page_xpath).get()

        if next_page:
            next_page_url = urljoin(response.url, next_page.strip())
            yield scrapy.Request(next_page_url, callback=self.parse)
        else:
            self.logger.info(f"No next page found on {response.url}")

    def closed(self, reason):
        """Called when the spider finishes — log time and memory usage."""

        end_time = time.time()
        execution_time = end_time - self.start_time
        memory_usage = psutil.Process().memory_info().rss / (1024 * 1024)

        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Execution Time: {execution_time:.2f} seconds")
        self.logger.info(f"Memory Usage: {memory_usage:.2f} MB")

