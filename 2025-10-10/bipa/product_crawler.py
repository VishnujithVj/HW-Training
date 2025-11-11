import logging
import requests
from parsel import Selector
from mongoengine import connect
from items import ProductUrlItem, CategoryUrlItem
from settings import HEADERS, BASE_URL, PRODUCTS_PER_PAGE, MONGO_DB


class ProductCrawler:
    """Crawling Product URLs"""

    def __init__(self):
        """Initialize connections"""
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected successfully")

    def start(self):
        """Start crawling product URLs from category pages"""
        categories = CategoryUrlItem.objects()
        logging.info(f"Found {categories.count()} categories to process")

        for idx, category in enumerate(categories, 1):
            logging.info(f"[{idx}/{categories.count()}] Processing Category: {category.name}")
            self.process_category(category)

        self.close()

    def process_category(self, category):
        """Parse category with pagination"""
        page = 0
        empty_page_count = 0
        
        """ Stop after 2 consecutive empty pages """
        while empty_page_count < 2:  
            offset = page * PRODUCTS_PER_PAGE
            paged_url = f"{category.url}?offset={offset}"

            try:
                response = requests.get(paged_url, headers=HEADERS, timeout=30)
                
                if response.status_code != 200:
                    logging.warning(f"[{category.name}] Failed to fetch page {page + 1}")
                    break

                """ Check if page has products """
                has_products = self.parse_item(response, category)
                
                if has_products:
                    empty_page_count = 0  
                    page += 1
                else:
                    empty_page_count += 1
                    if empty_page_count < 2:  
                        page += 1
                        
            except requests.RequestException as e:
                logging.error(f"[{category.name}] Error fetching page {page + 1}: {e}")
                break

        logging.info(f"[{category.name}] Pagination completed at page {page}")

    """ PARSE ITEM """
    def parse_item(self, response, category):
        """Extract product URLs from a category page - returns True if products found"""
        sel = Selector(response.text)

        """ XPATH """
        PRODUCT_XPATH = '//a[contains(@href,"/p/")]/@href'

        """ EXTRACT """
        product_links = sel.xpath(PRODUCT_XPATH).getall()
        urls = self.clean_urls(product_links)

        if not urls:
            return False

        self.item_yield(urls, category)
        return True

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

    """ ITEM YIELD """
    def item_yield(self, urls, category):
        """Save product URLs to MongoDB"""
        saved_count = 0
        for url in urls:
            try:
                """ Check if URL already exists """
                if not ProductUrlItem.objects(url=url).first():
                    ProductUrlItem(url=url, category_url=category.url).save()
                    saved_count += 1
            except Exception as e:
                logging.warning(f"Failed to save URL {url}: {e}")
        
        logging.info(f"Saved {saved_count} new product URLs")

    def close(self):
        """Close connections"""
        logging.info("Product crawling completed")

if __name__ == "__main__":
    crawler = ProductCrawler()
    crawler.start()
    crawler.close()