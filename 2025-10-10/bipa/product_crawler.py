import logging
import requests
from parsel import Selector
from items import ProductUrlItem, CategoryUrlItem
from settings import HEADERS, BASE_URL, PRODUCTS_PER_PAGE


class ProductCrawler:
    """Crawling Product URLs in company-standard template"""

    # INIT
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.mongo = ''  


    # START
    def start(self):
        """Start crawling product URLs from category pages"""

        categories = CategoryUrlItem.objects()
        logging.info(f"Found {categories.count()} categories to process.")

        for idx, category in enumerate(categories, 1):
            logging.info(f"[{idx}/{categories.count()}] Processing Category: {category.name}")
            page = 0
            self.parse_category(category, page)

        self.close()


    # CLOSE
    def close(self):
        """Close session"""
        self.session.close()
        logging.info("Product crawling completed")


    # PARSE ITEM 
    def parse_category(self, category, page):
        """Parse category with pagination"""

        while True:
            offset = page * PRODUCTS_PER_PAGE
            paged_url = f"{category.url}?offset={offset}"

            response = self.session.get(paged_url)
            if response.status_code != 200:
                logging.warning(f"[{category.name}] Failed to fetch page {page + 1}")
                break

            is_next = self.parse_item(response, category)
            if not is_next:
                logging.info(f"[{category.name}] Pagination completed at page {page + 1}")
                break

            page += 1


    # XPATH
    def parse_item(self, response, category):
        """Extract product URLs from a category page"""
        sel = Selector(response.text)

        PRODUCT_XPATH = '//a[contains(@href,"/p/")]/@href'

        product_links = sel.xpath(PRODUCT_XPATH).getall()
        urls = self.clean_urls(product_links)

        if not urls:
            return False

        self.item_yield(urls, category)
        return True

    # CLEAN
    def clean_urls(self, links):
        """Normalize and deduplicate product URLs"""
        clean_urls = []
        for link in links:
            if not link or "/p/" not in link:
                continue

            if link.startswith("/"):
                full_url = BASE_URL.rstrip("/") + link.split("?")[0]
            else:
                full_url = link.split("?")[0]

            if full_url.startswith("http") and full_url not in clean_urls:
                clean_urls.append(full_url)

        return list(set(clean_urls))

    # ITEM YIELD
    def item_yield(self, urls, category):
        """Save product URLs to MongoDB"""
        for url in urls:
            try:
                ProductUrlItem(url=url, category_url=category.url).save()
            except Exception as e:
                logging.warning(f"Failed to save URL {url}: {e}")


# ENTRY POINT
if __name__ == "__main__":
    crawler = ProductCrawler()
    crawler.start()
