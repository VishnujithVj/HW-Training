import logging, re
from datetime import datetime
from urllib.parse import urljoin
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductItem, ProductUrlItem
from settings import HEADERS, MONGO_DB, BASE_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

class ProductParser:
    """Extracts product details from URLs"""
    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")

    def start(self):
        products = ProductUrlItem.objects.all()
        if not products:
            return

        logging.info(f"Found {len(products)} products to parse")

        for product in products:
            url = product.product_url
            if not url: continue
            logging.info(f"Parsing: {url}")
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                self.parse_product(url, response)
            else:
                logging.warning(f"Failed: {response.status_code} {url}")

    def parse_product(self, url, html):
        """Extract product details"""
        select = Selector(html.text)
        clean = lambda t: re.sub(r"\s+", " ", t).strip() if t else ""
        get = lambda xp: clean(select.xpath(xp).get())
        getall = lambda xp: [clean(x) for x in select.xpath(xp).getall() if x.strip()]

        unique_id = get('//h2[contains(text(),"Product Code")]/following-sibling::span/text()')
        name = get('//h1[@data-testid="product-title"]/text()')
        price_now = get('//div[@data-testid="product-now-price"]//span/text()')
        price_was = get('//div[@data-testid="product-was-price"]/text()')
        promo_date = get('//table//p[@data-testid="price-history-date-0"]/text()')
        desc = clean(" ".join(select.xpath('//div[@data-testid="item-description-tone-of-voice"]//text()').getall()))
        care_data = getall('//h2[contains(.,"Care")]/ancestor::div[contains(@class,"MuiAccordion-root")]//p/text()')
        images = [urljoin(BASE_URL, i) for i in select.xpath('//div[@data-testid="image-gallery-slide"]//img/@src').getall()]

        material = " ".join([t for t in care_data if "%" in t or "cotton" in t.lower()])
        care = " ".join([t for t in care_data if t not in material])

        instock = "Add" in (get('//button[contains(@data-testid,"add-to-bag")]/text()') or "")
        rating = re.search(r'([\d\.]+)', select.xpath('//figure[@role="img"]/@aria-label').get() or "")
        review = re.search(r'\d+', select.xpath('//span[@data-testid="rating-style-badge"]/text()').get() or "")

        price = lambda v: float(re.search(r"([\d\.]+)", v).group(1)) if v and re.search(r"([\d\.]+)", v) else None
        current_price, original_price = price(price_now), price(price_was)
        promo_price = current_price if original_price and current_price and original_price != current_price else None

        item = {
            "unique_id": unique_id,
            "competitor_name": "FatFace",
            "store_name": "FatFace Online",
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "product_name": name,
            "brand": "FatFace",
            "regular_price": original_price or current_price,
            "selling_price": current_price,
            "promotion_price": promo_price,
            "promotion_valid_from": promo_date,
            "promotion_type": "Sale" if promo_price else "",
            "product_description": desc,
            "material_composition": material,
            "care_instructions": care,
            "rating": rating.group(1) if rating else "",
            "review": review.group(0) if review else "",
            "instock": instock,
            "pdp_url": url,
            "currency": "GBP",
            "image_url_1": images[0] if len(images) > 0 else "",
            "image_url_2": images[1] if len(images) > 1 else "",
            "image_url_3": images[2] if len(images) > 2 else "",
            "competitor_product_key": unique_id,
            "product_unique_key": f"{unique_id}P",
        }

        try:
            ProductItem(**item).save()
            logging.info(f"Saved: {unique_id}")
        except Exception as e:
            logging.error(f"Save error for {url}: {e}")

    def close(self):
        logging.info("MongoDB closed")

if __name__ == "__main__":
    parser = ProductParser()
    parser.start()
    parser.close()
