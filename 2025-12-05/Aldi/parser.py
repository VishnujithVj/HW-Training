import time
import re
import logging
import requests
from pymongo import MongoClient
from datetime import datetime
from parsel import Selector
from settings import (MONGO_URI,MONGO_DB,MONGO_COLLECTION_URLS,MONGO_COLLECTION_DATA,MONGO_COLLECTION_URL_FAILED,MONGO_COLLECTION_VARIANTS,PDP_API,HEADERS,)

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s:%(message)s",datefmt="%Y-%m-%d %H:%M:%S",)


class Parser:
    """Parser for Aldi product details"""

    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.mongo = self.client[MONGO_DB]
        logging.info("MongoDB successfully connected")


    def request_with_retry(self, url, headers=None, max_retries=3, timeout=20):
        """Retry wrapper for API & HTML requests"""
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, headers=headers, timeout=timeout)
                if resp.status_code == 200:
                    return resp
                else:
                    logging.warning(f"Attempt {attempt}: HTTP {resp.status_code} for {url}")
            except Exception as e:
                logging.warning(f"Attempt {attempt}: Error fetching {url} -> {e}")
            time.sleep(attempt)
        return None
    

    def start(self):
        metas = list(self.mongo[MONGO_COLLECTION_URLS].find({}))

        if not metas:
            logging.warning("No URLs found")
            return False

        logging.info(f"Found {len(metas)} URLs")

        for meta in metas:
            url = meta.get("product_url")
            sku = meta.get("sku")

            if not sku:
                logging.warning(f"Skipping URL with missing SKU: {url}")
                continue

            logging.info(f"Processing SKU: {sku} | URL: {url}")

            api_url = PDP_API.format(SKU=sku)
            response = self.request_with_retry(api_url, headers=HEADERS)

            if response:
                self.parse_item(url, response, meta)
            else:
                logging.warning(f"Failed to fetch product after retries: {sku}")
                self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one(
                    {"url": url, "sku": sku, "reason": "Request failed after retries"}
                )

            time.sleep(0.2)

        logging.info("Parser completed successfully")
        return True
    

    def parse_item(self, url, response, meta):
        """Parse product details from PDP API response"""

        data = response.json().get("data", {})
        if not data:
            logging.warning(f"No data found for {url}")
            return

        """XPATH"""
        IMAGE_URLS_XPATH = "//img[contains(@class,'product-image__image')]/@src"
        ALCOHOL_BY_VOLUME_XPATH = "//span[@data-test='alcohol-by-volume-value']/text()"

        """PRICE CLEANING"""
        price_data = data.get("price") or {}

        def clean_price(val):
            if not val:
                return ""
            return val.replace("£", "").strip()

        amount_relevant = price_data.get("amountRelevantDisplay", "")
        amount_regular = price_data.get("amountWasDisplay", amount_relevant)
        comparison_display = price_data.get("comparisonDisplay", "")

        selling_price = clean_price(amount_relevant)
        regular_price = clean_price(amount_regular)
        price_per_unit = clean_price(comparison_display)

        """DESCRIPTION"""
        raw_desc = data.get("description") or ""
        clean_html = (
            raw_desc.replace("<CRLF>", " ")
                    .replace("&nbsp;", " ")
                    .replace("\t", " ")
        )
        clean_html = re.sub(r'<span[^>]*id="cke_bm_.*?</span>', "", clean_html, flags=re.DOTALL)
        clean_html = re.sub(r"<li>\s*</li>", "", clean_html)

        text = Selector(text=clean_html).xpath("//text()[normalize-space()]").getall()
        clean_description = re.sub(r"\s+", " ", " ".join(text)).strip()

        """GRAMMAGE SPLIT"""
        size_raw = data.get("sellingSize", "")
        grammage_quantity = ""
        grammage_unit = ""

        if size_raw:
            parts = size_raw.split()
            if len(parts) >= 2:
                grammage_quantity = parts[0].strip()
                grammage_unit = parts[1].strip()

        """CATEGORY HANDLING"""
        categories = data.get("categories", [])
        clean_names = ["Home"]

        for cat in categories:
            name = cat.get("name", "").strip()
            if name:
                clean_names.append(name)

        producthierarchy_level_1 = clean_names[0] if len(clean_names) > 0 else ""
        producthierarchy_level_2 = clean_names[1] if len(clean_names) > 1 else ""
        producthierarchy_level_3 = clean_names[2] if len(clean_names) > 2 else ""
        producthierarchy_level_4 = clean_names[3] if len(clean_names) > 3 else ""

        breadcrumb = " > ".join(clean_names)

        """IMAGE URLs"""
        html_response = self.request_with_retry(url, headers=HEADERS)

        image_url_1 = ""
        if html_response:
            sel = Selector(text=html_response.text)
            image_urls = sel.xpath(IMAGE_URLS_XPATH).getall()
            image_url_1 = image_urls[0] if image_urls else ""

        """ALCOHOL BY VOLUME"""
        alcohol_value = ""

        if html_response:
            sel = Selector(text=html_response.text)
            abv_raw = sel.xpath(ALCOHOL_BY_VOLUME_XPATH).get() or ""
            alcohol_value = abv_raw.replace('%', '').strip() 

        """DATE EXTRACTION"""
        extraction_date = datetime.today().strftime("%Y-%m-%d")

        """VARIANTS HANDLING"""
        parent_sku = str(data.get("sku", ""))
        parent_name = data.get("name", "")
        parent_brand = data.get("brandName", "")
        url_slug = data.get("urlSlugText", "")
        
        variant_names = []
        variants_data = data.get("variants", {})
        
        if variants_data:
            buckets = variants_data.get("buckets", [])
            options = variants_data.get("options", [])
            
            if buckets and options:
                variant_type = buckets[0].get("label", "")
                variant_values = buckets[0].get("values", [])
                variant_names = variant_values
                
                """Store variants in separate collection"""
                for idx, variant_value in enumerate(variant_values):
                    if idx < len(options) and options[idx]:
                        variant_sku = options[idx][0].get("sku", "")
                        if variant_sku:
                            variant_doc = {
                                "parent_sku": parent_sku,
                                "parent_name": parent_name,
                                "parent_brand": parent_brand,
                                "variant_sku": variant_sku,
                                "variant_name": f"{parent_name} - {variant_value}",
                                "variant_type": variant_type,
                                "variant_value": variant_value,
                                "extraction_date": extraction_date,
                                "pdp_url": f"https://www.aldi.co.uk/product/{url_slug}-{variant_sku}",
                                "display_info": f"{parent_brand} - {parent_name} - {variant_value} (SKU: {variant_sku})"
                            }
                            
                            try:
                                self.mongo[MONGO_COLLECTION_VARIANTS].insert_one(
                                    {"variant_sku": variant_sku},
                                    {"$set": variant_doc},
                                    upsert=True
                                )
                                logging.info(f"Stored variant: {variant_value} (SKU: {variant_sku})")
                            except Exception as e:
                                logging.error(f"Failed to insert variant: {e}")

        """ITEM YIELD"""
        item = {}
        item["unique_id"] = parent_sku
        item["competitor_name"] = "Aldi"
        item["store_name"] = ""
        item["extraction_date"] = extraction_date
        item["product_name"] = parent_name
        item["brand"] = parent_brand
        item["grammage_quantity"] = grammage_quantity
        item["grammage_unit"] = grammage_unit
        item["producthierarchy_level1"] = producthierarchy_level_1
        item["producthierarchy_level2"] = producthierarchy_level_2
        item["producthierarchy_level3"] = producthierarchy_level_3
        item["producthierarchy_level4"] = producthierarchy_level_4
        item["regular_price"] = regular_price
        item["selling_price"] = selling_price
        item["price_per_unit"] = price_per_unit
        item["currency"] = "GBP"
        item["breadcrumb"] = breadcrumb.replace(" >", ">").replace("> ", ">")
        item["pdp_url"] = url
        item["variants"] = ", ".join(variant_names) if variant_names else ""
        item["product_description"] = clean_description
        item["storage_instructions"] = data.get("storageInstructions", "")
        item["country_of_origin"] = data.get("countryOrigin", "")
        item["packaging"] = data.get("sellingSize", "")
        item["image_url_1"] = image_url_1
        item["competitor_product_key"] = parent_sku
        item["alchol_by_volume"] = alcohol_value
        item["site_shown_uom"] = data.get("sellingSize", "")
        item["ingredients"] = data.get("ingredients", "")
        item["product_unique_key"] = f"{parent_sku}P"

        logging.info(f"Inserted product: {item['product_name']}")

        try:
            self.mongo[MONGO_COLLECTION_DATA].insert_one(item)
        except Exception as e:
            logging.error(f"Failed to insert item: {e}")

    def close(self):
        self.mongo.client.close()
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()