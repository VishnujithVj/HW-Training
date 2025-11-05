import logging
import math
import time
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductUrlItem, CategoryUrlItem
from settings import BASE_URL, HEADERS, MONGO_DB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class ProductCrawler:
    """Product URL Crawler"""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")

    def start(self):
        """Requesting Start url"""
        subcategories = CategoryUrlItem.objects.all()
        if not subcategories:
            logging.error("No subcategories found. Run category crawler first.")
            return

        logging.info(f"Starting crawl for {len(subcategories)} subcategories")

        for subcategory in subcategories:
            meta = {}
            meta['category_url'] = subcategory.category_url
            meta['subcategory_url'] = subcategory.subcategory_url
            meta['page'] = 1  

            self.crawl_subcategory(meta)

    def crawl_subcategory(self, meta):
        """Crawl all pages of a subcategory"""
        seen_urls = set()

        while True:
            page_url = f"{meta['subcategory_url'].split('?')[0]}?p={meta['page']}"
            logging.info(f"Page {meta['page']}: {page_url}")

            response = requests.get(page_url, headers=HEADERS)
            if response.status_code == 200:
                has_next = self.parse_page(response, meta, seen_urls)
                if not has_next:
                    logging.info("Pagination completed")
                    break

                """ pagination crawling """
                meta['page'] += 1
                time.sleep(1)

            else:
                logging.warning(f"Non-200 response: {response.status_code}")
                break

    def parse_page(self, response, meta, seen_urls):
        """Parse product URLs from page"""
        sel = Selector(response.text)

        """ XPATH """
        PRODUCT_URL_XPATH = '//a[contains(@class,"MuiCardMedia-root")]/@href'

        """ EXTRACT """
        product_urls = sel.xpath(PRODUCT_URL_XPATH).getall()
        product_urls = [urljoin(BASE_URL, url.split('#')[0]) for url in product_urls if url.strip()]

        if product_urls:
            new_urls = [url for url in product_urls if url not in seen_urls]
            
            if new_urls:
                seen_urls.update(new_urls)
                
                """ ITEM SAVE """
                for url in new_urls:
                    item_data = {
                        "product_url": url,
                        "page_no": meta['page'],
                        "subcategory_url": meta['subcategory_url'],
                        "category_url": meta['category_url'],
                    }
                    
                    try:
                        item = ProductUrlItem(**item_data)
                        item.save()
                        logging.info(f"Saved: {url}")
                    except Exception as e:
                        logging.error(f"Error saving {url}: {e}")

                logging.info(f"Page {meta['page']}: {len(new_urls)} new URLs saved")

            """ Check if should continue pagination """
            if meta['page'] == 1:
                total_products = self.get_total_products(sel)
                if total_products:
                    per_page = len(product_urls)
                    total_pages = math.ceil(total_products / per_page) if per_page else 1
                    if meta['page'] >= total_pages:
                        return False

            return True
        
        return False

    def get_total_products(self, selector):
        """Get total product count from first page"""
        count_text = selector.xpath('//span[@class="esi-count"]/text()').get()
        if count_text:
            digits = ''.join(filter(str.isdigit, count_text))
            return int(digits) if digits else 0
        return 0

    def close(self):
        """Close function for all module object closing"""
        self.mongo.close()


if __name__ == "__main__":
    crawler = ProductCrawler()
    crawler.start()
    crawler.close()