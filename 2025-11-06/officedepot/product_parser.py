import logging
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductUrlItem, ProductItem, ProductFailedItem
from settings import HEADERS, MONGO_DB


class Parser:
    """Parse and save detailed product data."""

    def __init__(self):
        self.db = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected successfully")

    def start(self):
        """Fetch product URLs and parse each one."""
        products = ProductUrlItem.objects()

        if not products:
            logging.warning("No product URLs found in DB")
            return

        for product in products:
            logging.info(f"Parsing: {product.product_name} ({product.url})")
            try:
                self.parse_product(product)
            except Exception as e:
                logging.error(f"Error parsing {product.url}: {e}")
                ProductFailedItem(url=product.url).save()

    def parse_product(self, product):
        """Extract and save product details."""
        response = requests.get(product.url, headers=HEADERS, impersonate="chrome124", timeout=30)

        if response.status_code != 200:
            logging.warning(f"Status {response.status_code} for {product.url}")
            ProductFailedItem(url=product.url).save()
            return

        select = Selector(text=response.text)

        specs = {}
        for row in select.xpath('//tr[@class="sku-row"]'):
            key = row.xpath('normalize-space(td[1]/text())').get()
            value = row.xpath('normalize-space(td[2]/text())').get()
            if key and value:
                specs[key] = value

        manufacturer = specs.get("manufacturer", "")
        brand = specs.get("brand name", "")
        mpn = specs.get("Manufacturer #", "")
        model_no = specs.get("Item #", "")
        qty_per_uoi = specs.get("Number of Markers Per Pack/Box", "")
        description_parts = select.xpath('//div[@class="sku-description"]//text()').getall()
        description = " ".join([d.strip() for d in description_parts if d.strip()])
        name = select.xpath('//h1[@class="od-heading od-heading-h1 sku-heading"]/text()').get()
        price = (select.xpath('//span[contains(@class,"od-graphql-price-big-price")]/text()').get()
                  or select.xpath('//*[contains(@class,"price") and contains(text(),"$")]/text()').get())

        data = {
            "company_name": "Office Depot",
            "manufacturer_name": manufacturer or "",
            "brand_name": brand or "",
            "vendor_seller_part_number": "",
            "item_name": (name or "").strip(),
            "full_product_description": description,
            "price": (price or "").strip(),
            "qty_per_uoi": (qty_per_uoi or "").strip(),
            "product_category": product.category_name or "",
            "url": product.url,
            "manufacturer_part_number": mpn or "",
            "country_of_origin": "",
            "model_number": model_no or "",
        }
        
        """Check for existing product and save"""
        existing = ProductItem.objects(url=product.url).first()
        if existing:
            logging.info(f"Product already exists: {product.url}")
        else:
            ProductItem(**data).save()
            logging.info(f"Saved product: {name or 'Unnamed'}")

    def close(self):
        self.db.close()
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    parser = Parser()
    parser.start()
    parser.close()
