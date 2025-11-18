import logging
import requests
from urllib.parse import urljoin, urlparse, parse_qs
from parsel import Selector
from mongoengine import connect
from settings import BASE_URL, HEADERS, MONGO_DB, MONGO_HOST
from items import ProductUrlItem


class Crawler:

    def __init__(self):
        self.mongo = connect(db=MONGO_DB, host=MONGO_HOST)
        logging.info("MongoDB connected")

    def start(self):
        urls = [
            f"{BASE_URL}/vehicles/new-arrivals",
            f"{BASE_URL}/vehicles",
            f"{BASE_URL}/vehicles/sold",
        ]

        for category_url in urls:
            category = (
                "new" if "/new-arrivals" in category_url else
                "sold" if "/sold" in category_url else
                "current")

            meta = {
                "category": category,"category_url": category_url,"page": 1,}

            page_url = category_url
            while True:
                logging.info(f"Fetching: {page_url}")

                try:
                    response = requests.get(page_url, headers=HEADERS, timeout=15)
                except Exception as e:
                    logging.error(f"Request error: {e}")
                    break

                if response.status_code != 200:
                    logging.error(f"Bad status: {response.status_code}")
                    break

                if not self.parse_item(response, meta):
                    break

                sel = Selector(response.text)
                next_page = sel.xpath("//li[contains(@class,'next')]/a/@href").get()
                if not next_page:
                    break

                page_url = urljoin(BASE_URL, next_page)
                params = parse_qs(urlparse(page_url).query)
                meta["page"] = int(params.get("page", [meta["page"] + 1])[0])

    def parse_item(self, response, meta):
        sel = Selector(response.text)

        links = sel.xpath(
            "//a[contains(@href,'/vehicles/')]/@href"
        ).getall()

        if not links:
            return False

        skip_categories = {
            f"{BASE_URL}/vehicles",
            f"{BASE_URL}/vehicles/new-arrivals",
            f"{BASE_URL}/vehicles/sold"
        }

        for href in links:
            full = urljoin(BASE_URL, href).split("?")[0]
            if full in skip_categories:
                continue

            if ProductUrlItem.objects(url=full).first():
                continue

            try:
                ProductUrlItem(
                    url=full,
                    category=meta["category"],
                    category_url=meta["category_url"],  
                    page_no=meta["page"]
                ).save()

                logging.info(
                    f"Saved URL: {full} | {meta['category']} | page {meta['page']}"
                )

            except Exception as e:
                logging.error(f"Save error: {e}")

        return True

    def close(self):
        logging.info("Crawler closed.")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
