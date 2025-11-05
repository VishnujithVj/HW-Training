import logging
import re
from datetime import datetime
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductItem, ProductUrlItem
from settings import HEADERS, MONGO_DB, BASE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Parser:
    """Product Parser"""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")

    def start(self):
        """Start parsing product URLs"""
        product_urls = ProductUrlItem.objects.all()
        if not product_urls:
            logging.error("No product URLs found. Run product crawler first.")
            return

        logging.info(f"Found {len(product_urls)} product URLs to parse")

        for product in product_urls:
            url = product.product_url
            if not url:
                continue

            logging.info(f"Parsing product: {url}")
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                self.parse_item(url, response)
            else:
                logging.warning(f"Failed to fetch {url}, status: {response.status_code}")

    def parse_item(self, url, response):
        """Parse product details from HTML"""
        sel = Selector(text=response.text)

        """ XPATH """
        UNIQUE_ID_XPATH = '//h2[contains(text(),"Product Code")]/following-sibling::span/text()'
        PRODUCT_NAME_XPATH = '//h1[@data-testid="product-title"]/text()'
        PRICE_NOW_XPATH = '//div[@data-testid="product-now-price"]//span/text()'
        PRICE_WAS_XPATH = '//div[@data-testid="product-was-price"]/text()'
        PROMO_DATE_XPATH = '//table//p[@data-testid="price-history-date-0"]/text()'
        DESCRIPTION_XPATH = '//div[@data-testid="item-description-tone-of-voice"]//text()'
        CARE_FABRIC_XPATH = '//h2[contains(.,"Care")]/ancestor::div[contains(@class,"MuiAccordion-root")]//p/text()'
        IMAGES_XPATH = '//div[@data-testid="image-gallery-slide"]//img/@src'
        INSTOCK_XPATH = '//button[contains(@data-testid,"add-to-bag")]/text()'
        RATING_XPATH = '//figure[@role="img" and contains(@aria-label, "Stars")]'
        REVIEW_XPATH = '//span[@data-testid="rating-style-badge"]'

        """ EXTRACT """
        unique_id = self.clean_text(sel.xpath(UNIQUE_ID_XPATH).get())
        if not unique_id:
            logging.warning(f"No unique_id found on {url}")
            return

        product_name = self.clean_text(sel.xpath(PRODUCT_NAME_XPATH).get())
        price_now = sel.xpath(PRICE_NOW_XPATH).get()
        price_was = sel.xpath(PRICE_WAS_XPATH).get()
        promo_date = self.clean_text(sel.xpath(PROMO_DATE_XPATH).get())
        
        description = " ".join(sel.xpath(DESCRIPTION_XPATH).getall())
        description = self.clean_text(description)

        care_fabric_texts = sel.xpath(CARE_FABRIC_XPATH).getall()
        care_fabric_texts = [self.clean_text(t) for t in care_fabric_texts if t.strip()]
        
        material = ""
        care = ""
        for t in care_fabric_texts:
            if "cotton" in t.lower() or "%" in t:
                material += (t + " ")
            else:
                care += (t + " ")

        images = sel.xpath(IMAGES_XPATH).getall()
        images = [urljoin(BASE_URL, i) for i in images if i.strip()]

        """ RATING AND REVIEW EXTRACTION """
        rating = ""
        review = ""

        rating_figure = sel.xpath(RATING_XPATH)
        if rating_figure:
            aria_label = rating_figure.xpath('./@aria-label').get()
            if aria_label:
                rating_match = re.search(r'([\d\.]+)\s*Stars?', aria_label)
                if rating_match:
                    rating = rating_match.group(1)

        review_badge = sel.xpath(REVIEW_XPATH)
        if review_badge:
            review_text = review_badge.xpath('string(.)').get()
            if review_text:
                review_match = re.search(r'\(?(\d+)\)?', review_text)
                if review_match:
                    review = review_match.group(1)

        instock_text = sel.xpath(INSTOCK_XPATH).get()
        instock = "Add" in (instock_text or "")

        """ PRICE """
        selling_price = self.format_price(price_now)
        regular_price = self.format_price(price_was) or selling_price
        
        has_discount = bool(price_was and price_now and price_was != price_now)
        promotion_price = selling_price if has_discount else None  
        price_was_val = regular_price if has_discount else None    

        """ ITEM SAVE """
        item = {
            "unique_id": unique_id,
            "competitor_name": "FatFace",
            "store_name": "FatFace Online",
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "product_name": product_name,
            "brand": "FatFace",
            "regular_price": regular_price,
            "selling_price": selling_price,
            "promotion_price": promotion_price,  
            "price_was": price_was_val,          
            "promotion_valid_from": promo_date,
            "promotion_type": "Sale" if has_discount else "",
            "product_description": description,
            "material_composition": material.strip(),
            "care_instructions": care.strip(),
            "rating": rating or "",
            "review": review or "",
            "instock": instock,
            "pdp_url": url,
            "file_name_1": f"{unique_id}_1.png" if len(images) > 0 else "",
            "image_url_1": images[0] if len(images) > 0 else "",
            "file_name_2": f"{unique_id}_2.png" if len(images) > 1 else "",
            "image_url_2": images[1] if len(images) > 1 else "",
            "file_name_3": f"{unique_id}_3.png" if len(images) > 2 else "",
            "image_url_3": images[2] if len(images) > 2 else "",
            "competitor_product_key": unique_id,
            "product_unique_key": f"{unique_id}P",
            "currency": "GBP",
        }

        try:
            product_item = ProductItem(**item)
            product_item.save()
            logging.info(f"Successfully saved product: {unique_id}")
        except Exception as e:
            logging.error(f"Error saving product data for {url}: {e}")

    def clean_text(self, text):
        return re.sub(r"\s+", " ", text).strip() if text else ""

    def format_price(self, value):
        """Convert '£22' -> 22.0, return None for empty values"""
        if not value:
            return None
        match = re.search(r"([\d\.]+)", value)
        return float(match.group(1)) if match else None  

    def close(self):
        """Close connections"""
        self.mongo.close()


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()