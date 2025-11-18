import logging
import time
import requests
from parsel import Selector
from mongoengine import connect
from items import ProductUrlItem, ProductItem, ProductFailedItem
from settings import HEADERS, MONGO_DB, MONGO_HOST

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")
logging.getLogger("requests").setLevel(logging.WARNING)


class Parser:

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host=MONGO_HOST)
        logging.info("MongoDB connected")

    def start(self):
        metas = [{"url": item.url.strip()} for item in ProductUrlItem.objects()]
        for meta in metas:
            url = meta.get("url")
            logging.info(f"Parsing: {url}")

            response = self.fetch(url)
            if not response:
                logging.error(f"FAILED: {url} (fetch_failed)")
                ProductFailedItem(url=url, reason="fetch_failed").save()
                continue

            try:
                data = self.parse_item(url, response)
                if data:
                    self.save_item(url, data)
            except Exception as e:
                logging.exception(f"Parser error: {url}")
                ProductFailedItem(url=url, reason=str(e)).save()

            time.sleep(1)

    def fetch(self, url, attempts=3):
        """fetch url with retry"""
        for attempt in range(attempts):
            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                if response.status_code == 200:
                    return response.text
                logging.warning(f"Attempt {attempt+1}: Status {response.status_code} for {url}")
            except Exception as e:
                logging.warning(f"Attempt {attempt+1} error: {e}")
        return None

    def parse_item(self, url, html):
        sel = Selector(text=html)

        # XPATH
        HIGHLIGHTS_XPATH = "//div[@class='vehicle-description']/p[1]//text()"
        YEAR_XPATH = "//h1[@class='year-make']/span[@class='year']/text()"
        MAKE_XPATH = "//h1[@class='year-make']/span[@class='make']/text()"
        MODEL_XPATH = "//h1[@class='year-make']/span[@class='model']/text()"
        PRICE_XPATH = "//div[@class='price']/text()"
        SOLD_PRICE_XPATH = "//div[@class='vehicle-sold-banner']/text()"
        MILEAGE_XPATH = "//div[dt[text()='Miles']]/dd/text()"
        ENGINE_XPATH = "//div[dt[text()='Engine Size']]/dd/text()"
        TRANSMISSION_XPATH = "//div[dt[text()='Transmission Type']]/dd/text()"
        COLOR_XPATH = "//div[dt[text()='Body Color']]/dd/text()"
        FUEL_TYPE_XPATH = "//div[dt[text()='Engine Type']]/dd/text()"
        BODY_STYLE_XPATH = "//div[dt[text()='Body Style']]/dd/text()"
        VIN_XPATH = "//div[@class='spec vin']/dd/text()"
        IMAGE_XPATH = "//img[contains(@src,'cdn.dealeraccelerate.com')]/@src"

        # EXTRACT
        highlights_raw = sel.xpath(HIGHLIGHTS_XPATH).getall()
        highlights = [line.strip(" *") for line in highlights_raw if line.strip()]

        # ITEM YIELD
        item = {
            "source_link": url,
            "year": (sel.xpath(YEAR_XPATH).get() or "").strip(),
            "make": (sel.xpath(MAKE_XPATH).get() or "").strip(),
            "model": (sel.xpath(MODEL_XPATH).get() or "").strip(),
            "price": ((sel.xpath(PRICE_XPATH).get() or "").strip()
                      or (sel.xpath(SOLD_PRICE_XPATH).get() or "").strip()),
            "mileage": (sel.xpath(MILEAGE_XPATH).get() or "").strip(),
            "engine": (sel.xpath(ENGINE_XPATH).get() or "").strip(),
            "transmission": (sel.xpath(TRANSMISSION_XPATH).get() or "").strip(),
            "color": (sel.xpath(COLOR_XPATH).get() or "").strip(),
            "fuel_type": (sel.xpath(FUEL_TYPE_XPATH).get() or "").strip(),
            "body_style": (sel.xpath(BODY_STYLE_XPATH).get() or "").strip(),
            "vin": (sel.xpath(VIN_XPATH).get() or "").strip(),
            "description": " ".join(highlights),
            "image_urls": [url_part.strip() for url_part in sel.xpath(IMAGE_XPATH).getall()],
        }

        logging.info(item)
        return item

    def save_item(self, url, data):
        existing = ProductItem.objects(source_link=url).first()
        clean_data = {k: v for k, v in data.items() if v not in (None, "", [])}

        if existing:
            existing.update(**clean_data)
            logging.info(f"Updated: {url}")
        else:
            ProductItem(**clean_data).save()
            logging.info(f"Saved new: {url}")

    def close(self):
        logging.info("Parser closed")


if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()
