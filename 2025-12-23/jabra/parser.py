import logging
import requests
from parsel import Selector
from pymongo import MongoClient
from settings import (
    PARSER_HEADERS, PARSER_TIMEOUT,
    MONGO_URI, MONGO_DB, MONGO_COLLECTION_PRODUCT_URLS,
    MONGO_COLLECTION_PRODUCT_DETAILS, MONGO_COLLECTION_GROUP_IDS,
    MONGO_COLLECTION_DOCUMENTS, MONGO_COLLECTION_DATA
)


class JabraProductParser:
    """Parsing Product Pages from Jabra Website"""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DB]

        self.product_urls_col = self.db[MONGO_COLLECTION_PRODUCT_URLS]
        self.product_details_col = self.db[MONGO_COLLECTION_PRODUCT_DETAILS]
        self.group_ids_col = self.db[MONGO_COLLECTION_GROUP_IDS]
        self.documents_col = self.db[MONGO_COLLECTION_DOCUMENTS]
        self.collection = self.db[MONGO_COLLECTION_DATA]

        self.headers = PARSER_HEADERS
        
        logging.info("Product Parser initialized")

    def start(self):
        """Start parsing product pages"""
        
        # Fetch all product URLs
        products = self.product_urls_col.find(
            {
                "product_url": {"$exists": True},
                "sku": {"$exists": True},
            }
        )

        for product in products:
            url = product.get("product_url")
            sku = product.get("sku")

            if not url or not sku:
                continue

            logging.info(f"Fetching page → {sku}")

            try:
                response = requests.get(url, headers=self.headers, timeout=PARSER_TIMEOUT)

                if response.status_code != 200:
                    logging.warning(f"Skipped {sku} | HTTP {response.status_code}")
                    continue

                selector = Selector(text=response.text)
                item = self.parse_item(selector, product)

                if item:
                    try:
                        self.collection.insert_one(item)
                        logging.info(f"Saved → {sku}")
                    except Exception as e:
                        logging.error(f"Failed to save {sku}: {e}")
                else:
                    logging.warning(f"No data parsed → {sku}")

            except requests.RequestException as e:
                logging.error(f"Request failed for {sku}: {e}")

    def parse_item(self, selector, product):
        """Parse product page and combine with database data"""
        
        sku = product.get("sku")

        # Fetch product details from database
        product_details = self.product_details_col.find_one(
            {"sku": sku}, {"_id": 0}
        ) or {}

        # Fetch pricing from group_ids
        group_price = self.group_ids_col.find_one(
            {"sku": sku}, {"_id": 0}
        ) or {}

        selling_price = group_price.get("c_discountedPrice")
        regular_price = group_price.get("c_listedPrice")
        currency = group_price.get("currency", "USD")

        # Fetch documents
        documents_cursor = self.documents_col.find(
            {"sku": sku, "fileUrl": {"$exists": True}},
            {"_id": 0, "fileUrl": 1}
        )

        documents = [
            doc["fileUrl"]
            for doc in documents_cursor
            if doc.get("fileUrl")
        ]

        # Initialize item
        item = {
            "product_name": product.get("product_name"),
            "product_url": product.get("product_url"),
            "sku": sku,
            "productId": product_details.get("productId"),
            "segmentType": product_details.get("segmentType"),
            "warranty": product_details.get("warranty"),
            "model": product_details.get("model"),
            "images": product_details.get("images"),
            "selling_price": selling_price,
            "regular_price": regular_price,
            "currency": currency,
            "documents": documents,
            "section_title": None,
            "features": [],
        }

        # XPATH - Extract section title
        SECTION_TITLE_XPATH = "//h2[contains(@class,'heading-2')]/text()"
        section_title = selector.xpath(SECTION_TITLE_XPATH).get()

        if not section_title:
            return None

        item["section_title"] = section_title.strip()

        # XPATH - Extract features
        FEATURE_BLOCKS_XPATH = (
            "//h2[contains(@class,'heading-2')]"
            "/following-sibling::div[1]//div[contains(@class,'flex gap-4')]"
        )
        FEATURE_TITLE_XPATH = ".//h3/text()"
        FEATURE_DESC_XPATH = ".//p/text()"

        feature_blocks = selector.xpath(FEATURE_BLOCKS_XPATH)

        for block in feature_blocks:
            title = block.xpath(FEATURE_TITLE_XPATH).get()
            description = block.xpath(FEATURE_DESC_XPATH).get()

            if title or description:
                item["features"].append({
                    "title": title.strip() if title else None,
                    "description": description.strip() if description else None
                })

        return item

    def stop(self):
        """Close MongoDB connection"""
        self.mongo.close()
        logging.info("Product Parser finished & MongoDB closed")


if __name__ == "__main__":
    parser = JabraProductParser()
    parser.start()
    parser.stop()