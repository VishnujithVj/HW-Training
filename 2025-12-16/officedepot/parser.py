import json
import time
import logging
from parsel import Selector
from curl_cffi import requests
from pymongo import MongoClient
from settings import (
    HEADERS,
    MONGO_DB,
    MONGO_COLLECTION_PRODUCT_URL,
    MONGO_COLLECTION_DATA,
    MONGO_COLLECTION_URL_FAILED,
)


class Parser:
    """Parses PDP JSON-LD and saves final product data"""

    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.mongo = self.client[MONGO_DB]
        logging.info("MongoDB connected")

    def start(self):
        for product in self.mongo[MONGO_COLLECTION_PRODUCT_URL].find():
            try:
                self.parse_item(product)
            except Exception as e:
                logging.error(f"Unhandled error: {e}")
                self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one(
                    {"url": product.get("url")}
                )

    def parse_item(self, product):
        response = None

        # -------- RETRY LOOP (FIXED) --------
        for attempt in range(1, 4):
            try:
                response = requests.get(
                    product["url"],
                    headers=HEADERS,
                    impersonate="chrome124",
                    timeout=30,
                )
                if response.status_code == 200:
                    break
            except Exception as e:
                logging.warning(
                    f"Request error | Attempt {attempt} | {product['url']} | {e}"
                )

            time.sleep(attempt * 2)  # sleep ONLY between retries

        if not response or response.status_code != 200:
            self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one(
                {"url": product["url"]}
            )
            return

        sel = Selector(response.text)

        # -------- XPATH CONSTANTS --------
        NO_OF_BATTERY_XPATH = (
            '//table[contains(@class,"sku-table")]//tr['
            'td[1][normalize-space(.)="Number of Batteries Per Pack/Box"]'
            ']/td[2]/text()'
        )

        BATTERY_TYPE_XPATH = (
            '//table[contains(@class,"sku-table")]//tr['
            'td[1][normalize-space(.)="Cell Type"]'
            ']/td[2]/text()'
        )

        # -------- JSON-LD (ROBUST) --------
        product_json = None
        for block in sel.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(block)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    product_json = data
                    break
            except json.JSONDecodeError:
                continue

        if not product_json:
            self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one(
                {"url": product["url"]}
            )
            return

        # -------- BASIC FIELDS --------
        sku = product_json.get("sku", "")
        name = product_json.get("name", "")
        description = product_json.get("description", "")
        brand = product_json.get("brand", "")
        product_url = product_json.get("@id") or product["url"]

        # -------- PRICE --------
        offers = product_json.get("offers", {}) or {}
        price = offers.get("price", "")
        currency = offers.get("priceCurrency", "USD")

        # -------- CATEGORY --------
        category = product.get("category_name", "")

        # -------- IMAGES --------
        image_url = ""
        image_data = product_json.get("image", {})
        if isinstance(image_data, dict):
            image_url = image_data.get("contentUrl", "")

        # -------- SKU TABLE EXTRACTION --------
        number_of_batteries = (
            sel.xpath(self.NO_OF_BATTERY_XPATH).get(default="") or ""
        ).strip()

        battery_type = (
            sel.xpath(self.BATTERY_TYPE_XPATH).get(default="") or ""
        ).strip()

        final_data = {
            "sku": sku,
            "product_title": name,
            "category": category,
            "site_url": product_url,
            "product_url": product_url,
            "cost": price,
            "currency": currency,
            "notes": description,
            "brand": brand,
            "battery_type": battery_type,
            "number_of_batteries": number_of_batteries,
            "product_cost_brand": price,
            "images": image_url,
            "company_name": "Office Depot",
        }

        # -------- DUPLICATE CHECK --------
        if self.mongo[MONGO_COLLECTION_DATA].find_one(
            {"product_url": product_url}
        ):
            return

        self.mongo[MONGO_COLLECTION_DATA].insert_one(final_data)
        logging.info(f"Saved product: {name}")

    def stop(self):
        self.client.close()
        logging.info("MongoDB closed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    parser = Parser()
    parser.start()
    parser.stop()
