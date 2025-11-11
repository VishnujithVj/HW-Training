import logging
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from settings import BASE_URL, MONGO_DB, HEADERS
from items import CategoryUrlItem


class Crawler:
    """Crawls all category names and URLs from the OfficeDepot homepage."""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected successfully.")

    def start(self):
        response = requests.get(BASE_URL, headers=HEADERS, impersonate="chrome124")

        if response.status_code == 200:
            self.parse_item(response)
        else:
            logging.error(f"Request failed with status {response.status_code}")

    def parse_item(self, response):
        """Extract category links and save."""
        sel = Selector(response.text)

        CATEGORY_XPATH = '//a[@class="od-menu-link"]'
        NAME_XPATH = './@title | normalize-space(.)'
        URL_XPATH = './@href'

        categories = sel.xpath(CATEGORY_XPATH)
        if not categories:
            logging.warning("No categories found on page.")
            return False

        """Clear existing category data"""
        CategoryUrlItem.objects.delete()

        saved_count = 0
        for cat in categories:
            name = cat.xpath(NAME_XPATH).get()
            href = cat.xpath(URL_XPATH).get()

            if not (name and href):
                continue

            CategoryUrlItem(
                name=name.strip(),
                url=urljoin(BASE_URL, href)
            ).save()
            saved_count += 1
            logging.info(f"Saved category: {name.strip()}")

        logging.info(f"Total categories saved: {saved_count}")
        return True

    def close(self):
        self.mongo.close()
        logging.info("MongoDB connection closed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    crawler = Crawler()
    crawler.start()
    crawler.close()
