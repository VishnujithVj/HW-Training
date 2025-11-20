import logging
import json
from curl_cffi import requests
from parsel import Selector
from mongoengine import connect
from items import ProductUrlItem, ProductItem, ProductFailedItem
from settings import HEADERS, MONGO_DB, MONGO_HOST


class Parser:
    def __init__(self):
        self.mongo = connect(db=MONGO_DB, host=MONGO_HOST)
        logging.info("MongoDB connected")

    def start(self):
        """Iterate over product URLs and parse details"""
        metas = [{"url": item.url.strip()} for item in ProductUrlItem.objects()]

        for meta in metas:
            url = meta.get("url")
            logging.info(f"Parsing: {url}")

            try:
                r = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=25)
                if r.status_code != 200:
                    logging.error(f"FAILED: {url} (fetch_failed)")
                    ProductFailedItem(url=url, reason="fetch_failed").save()
                    continue

                item = self.parse_item(url, r)
                if item:
                    self.save(url, item)

            except Exception as e:
                logging.exception(f"Parser error: {url}")
                ProductFailedItem(url=url, reason=str(e)).save()

        logging.info("Parsing completed")

    def parse_item(self, url, response):
        """Extract product details from HTML"""
        sel = Selector(response.text)

        # XPATH SECTION
        PRODUCT_NAME_XPATH = '//h1[@data-testid="product-name"]/text()'
        PRICE_XPATH = '//span[@data-testid="price"]/text()'
        WASPRICE_XPATH = '//span[contains(@class,"line-through")]/text()'
        BREADCRUMB_XPATH = '//div[contains(@class,"flex items-center")]/a/text()'
        DETAILS_XPATH = '//div[@data-testid="product-bullet-points"]//li/span/text()'
        PRODUCT_TYPE_XPATH = '//span[contains(text(),"Product Type")]/following-sibling::span/text()'
        JSONLD_XPATH = '//script[@type="application/ld+json"]/text()'
        SPEC_ROWS_XPATH = '//div[@data-testid="product-attribute-table"]/div/div[contains(@class,"flex")]'

        # EXTRACTION & CLEANING
        product_id = url.rstrip("/").split("/")[-1]
        name = sel.xpath(PRODUCT_NAME_XPATH).get(default="").strip()
        price = sel.xpath(PRICE_XPATH).get(default="")
        was_price = sel.xpath(WASPRICE_XPATH).get(default="")
        breadcrumb = " > ".join(x.strip() for x in sel.xpath(BREADCRUMB_XPATH).getall())
        details_string = " | ".join(d.strip() for d in sel.xpath(DETAILS_XPATH).getall())
        product_type = sel.xpath(PRODUCT_TYPE_XPATH).get(default="")

        # Images via JSON-LD
        images = []
        for script in sel.xpath(JSONLD_XPATH).getall():
            try:
                data = json.loads(script)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    img = data.get("image", [])
                    images.extend(img if isinstance(img, list) else [img])
            except Exception:
                pass

        # Specification Table
        specs = {}
        rows = sel.xpath(SPEC_ROWS_XPATH)
        for row in rows:
            label = row.xpath('.//span[1]/text()').get(default="").strip()
            val = row.xpath('.//span[2]/text()').get(default="").strip()
            if label:
                specs[str(label)] = str(val)   

        return {
            "product_id": product_id,
            "url": url,
            "product_name": name,
            "product_color": "",
            "material": "",
            "quantity": "",
            "details_string": details_string,
            "specification": specs,
            "product_type": product_type,
            "price": price,
            "wasPrice": was_price,
            "breadcrumb": breadcrumb,
            "image": images,
        }

    def save(self, url, item):
        """Save parsed product item to MongoDB"""
        ProductItem(**item).save()
        logging.info(f"Saved item: {url}")

    def close(self):
        """Close MongoDB connection"""
        self.mongo.close()
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()
