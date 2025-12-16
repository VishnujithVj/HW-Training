import logging
import json
import time
from curl_cffi import requests
from pymongo import MongoClient
from parsel import Selector
from settings import (HEADERS, MONGO_URI, MONGO_DB,MONGO_COLLECTION_MATCHED, MONGO_COLLECTION_DATA,REQUEST_DELAY, REQUEST_TIMEOUT)


class Parser:
    """Parser for extracting product details from PDP"""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(MONGO_URI)
        self.mongo = self.client[MONGO_DB]
        logging.info("Parser initialized with MongoDB connection")

    def start(self):
        
        items = list(self.mongo[MONGO_COLLECTION_MATCHED].find({}, {"_id": 0}))
        total_items = len(items)
        logging.info(f"Found {total_items} products to parse")

        metas = []
        for item in items:
            meta = {
                'url': item.get("product_url"),
                'product_name': item.get("product_name"),
                'db_ean': item.get("ean"),
                'match_type': item.get("match_type"),
                'score': item.get("score", 0)
            }
            metas.append(meta)

        for idx, meta in enumerate(metas, 1):
            url = meta.get('url')
            
            if not url:
                logging.warning(f"[{idx}/{total_items}] Skipping item without URL")
                continue

            logging.info(f"[{idx}/{total_items}] Parsing PDP: {url}")

            try:
                response = requests.get(
                    url,
                    headers=HEADERS,
                    impersonate="chrome",
                    timeout=REQUEST_TIMEOUT
                )

                if response.status_code == 200:
                    self.parse_item(
                        url,
                        response,
                        product_name=meta.get('product_name'),
                        db_ean=meta.get('db_ean'),
                        match_type=meta.get('match_type'),
                        score=meta.get('score')
    )

                else:
                    logging.warning(f"Failed to fetch PDP, status: {response.status_code}")
            except Exception as e:
                logging.error(f"Error fetching PDP: {str(e)}")

            time.sleep(REQUEST_DELAY)  
        logging.info("Parser completed!")


    def parse_item(self, url, response, product_name, db_ean, match_type, score):
        """Extract product details from PDP response"""
        sel = Selector(text=response.text)

        """ XPATH """
        BRAND_XPATH = '//div[contains(@class,"product_detail-brand")]//a/text()'
        BREADCRUMBS_XPATH_SCRIPTS = '//script[@type="application/ld+json"]/text()'
        BREADCRUMBS_XPATH_FALLBACK = '//ul[@id="breadcrumbs"]//li//span/text()'
        IMAGES_XPATH = '//div[@id="pdp_carousel"]//picture//img/@src'
        DESCRIPTION_XPATH = '//div[@class="product_detail-description"]//p/text()'
        MODEL_XPATH = '//div[contains(text(),"Modelo")]/text()'
        REFERENCE_XPATH = '//div[contains(text(),"Referencia")]/text()'
        ADDITIONAL_DETAILS_XPATH = '//div[contains(@class,"infoGroup")]'


        price = None
        ean = None
        brand = sel.xpath(BRAND_XPATH).get()

        """Extract Price and EAN from JSON-LD"""
        for block in sel.xpath(BREADCRUMBS_XPATH_SCRIPTS).getall():
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict) and data.get("@type") == "Product":
                    if "offers" in data and "price" in data["offers"]:
                        price = data["offers"]["price"]
                    if "sku" in data:
                        ean = str(data["sku"]).strip()
                    break
            except Exception:
                pass

        """CLEAN"""
        brand = brand.strip() if brand else None

        """ FILTER CONDITIONS """
        if db_ean:
            if not ean or str(db_ean) != str(ean):
                logging.info(f"EAN mismatch | DB: {db_ean} | PDP: {ean} | Skipped")
                return
        else:
            if score < 70:
                logging.info(f"Score below threshold ({score}%) | Skipped")
                return

        """Breadcrumbs"""
        breadcrumbs = []
        for block in sel.xpath(BREADCRUMBS_XPATH_SCRIPTS).getall():
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict) and data.get("@type") == "BreadcrumbList":
                    for bc in data.get("itemListElement", []):
                        breadcrumbs.append(bc["item"]["name"].strip())
                    break
            except Exception:
                pass

        if not breadcrumbs:
            breadcrumbs = sel.xpath(BREADCRUMBS_XPATH_FALLBACK).getall()
            breadcrumbs = [b.strip() for b in breadcrumbs if b.strip()]

        breadcrumbs_path = " > ".join(breadcrumbs) if breadcrumbs else None

        """ Images """
        images = sel.xpath(IMAGES_XPATH).getall()
        images = list(dict.fromkeys(images))

        """Description """
        description = sel.xpath(DESCRIPTION_XPATH).get()
        description = description.strip() if description else None

        """ Model and Reference """
        model = sel.xpath(MODEL_XPATH).get()
        reference = sel.xpath(REFERENCE_XPATH).get()

        if model:
            model = model.replace("Modelo:", "").strip()
        if reference:
            reference = reference.replace("Referencia:", "").strip()

        """ Additional Details """
        additional_details = {}
        info_blocks = sel.xpath(ADDITIONAL_DETAILS_XPATH)

        for block in info_blocks:
            key = block.xpath('.//dt[@class="titleInfoProduct"]/text()').get()
            value = block.xpath('.//dd//div/text()').get()
            if key and value:
                additional_details[key.strip()] = value.strip()


        """ ITEM YEILD """
        item = {}
        item["url"] = url
        item["product_name"] = product_name
        item["brand"] = brand
        item["price"] = price
        item["breadcrumbs"] = breadcrumbs_path
        item["images"] = images
        item["description"] = description
        item["model"] = model
        item["reference"] = reference
        item["ean"] = ean
        item["match_type"] = match_type
        item["score"] = score
        item["additional_details"] = additional_details
        
        logging.info(f"Saved product details: {product_name}")

        try:
            self.mongo[MONGO_COLLECTION_DATA].insert_one(item)
        except Exception as e:
            logging.error(f"Error saving product details: {str(e)}")


    def close(self):
        self.client.close()
        logging.info("MongoDB connection closed")
        
if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()