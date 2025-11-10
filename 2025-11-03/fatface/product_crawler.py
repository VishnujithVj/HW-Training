import logging, math, time
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductUrlItem, CategoryUrlItem
from settings import BASE_URL, HEADERS, MONGO_DB

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

class ProductCrawler:
    """Crawler to extract product URLs from subcategories"""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")

    def start(self):
        """Start crawling through all subcategories"""
        subcats = CategoryUrlItem.objects.all()
        if not subcats:
            logging.error("No subcategories found.")
            return
        logging.info(f"Found {len(subcats)} subcategories")

        for sub in subcats:
            meta = {"category_url": sub.category_url, "subcategory_url": sub.subcategory_url, "page": 1}
            self.crawl_pages(meta)

    def crawl_pages(self, meta):
        """Paginate through subcategory and extract product URLs"""
        seen_urls = set()

        while True:
            page_url = f"{meta['subcategory_url'].split('?')[0]}?p={meta['page']}"
            logging.info(f"Page {meta['page']}: {page_url}")

            response = requests.get(page_url, headers=HEADERS, timeout=30)
            if response.status_code != 200:
                logging.warning(f"Failed with statud code: {response.status_code}")
                break

            next = self.extract_and_save(response, meta, seen_urls)
            if not next:
                logging.info("Pagination completed")
                break

            meta["page"] += 1
            time.sleep(1)

    def extract_and_save(self, response, meta, seen_urls):
        """Extract and save product URLs"""
        select = Selector(response.text)
        urls = select.xpath('//a[contains(@class,"MuiCardMedia-root")]/@href').getall()
        full_urls = [urljoin(BASE_URL, u.split("#")[0]) for u in urls if u.strip()]
        if not urls: return False

        new_urls = [u for u in full_urls if u not in seen_urls]
        if not new_urls: return False
        seen_urls.update(new_urls)

        for url in new_urls:
            try:
                ProductUrlItem(
                    product_url=url,
                    page_no=meta["page"],
                    subcategory_url=meta["subcategory_url"],
                    category_url=meta["category_url"],
                ).save()

                logging.info(f"Saved: {url}")
            except Exception as e:
                logging.error(f"Error saving {url}: {e}")

        if meta["page"] == 1:
            total_product = self.get_total_count(select)
            if total_product and meta["page"] >= math.ceil(total_product / len(urls)):
                return False
        return True

    def get_total_count(self, select):
        """Extract total product count"""
        count_text = select.xpath('//span[@class="esi-count"]/text()').get()
        return int(''.join(filter(str.isdigit, count_text))) if count_text else 0

    def close(self):
        self.mongo.close()
        logging.info("MongoDB connection closed")

if __name__ == "__main__":
    crawler =ProductCrawler()
    crawler.start()
    crawler.close()
