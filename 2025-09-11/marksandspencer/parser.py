import requests
import re
import logging
from datetime import datetime
from parsel import Selector
from pymongo import MongoClient

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler()
    ]
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}
# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["marksandspencer"]

categories_col = db["categories"]
products_detail_col = db["products_detail"]

def parse_product(product_url):
    """Parse product data from a product page"""
    try:
        response = requests.get(product_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        sel = Selector(response.text)

        def safe_xpath(query, n=0, default="Not found"):
            result = sel.xpath(query).getall()
            return result[n].strip() if result and len(result) > n else default

        def safe_xpath_list(query, default=[]):
            result = sel.xpath(query).getall()
            return [item.strip() for item in result] if result else default

        product_color = sel.xpath('//span[@class="media-0_textSm__Q52Mz"]/text()').getall()

        # Regex fields
        raw_text = sel.get()
        material_match = re.search(r"(Cotton|Polyester|Silk|Linen|Wool)", raw_text, re.IGNORECASE)
        care_match = re.search(r"(Machine wash|Dry clean|Hand wash)", raw_text, re.IGNORECASE)
    
        product_data = {
            "unique_id": safe_xpath('//p[@class="media-0_textXs__ZzHWu"]/text()', 1),
            "product_name": safe_xpath('//h1/text()'),
            "brand": safe_xpath('//p[contains(@class,"brand-title_title__u6Xx5")]/text()', 0, "Marks & Spencer"),
            "category": safe_xpath('(//li[@class="breadcrumb_listItem__oW_Gf"]/a)[last()]/text()'),
            "breadcrumb": ", ".join(safe_xpath_list('//li[@class="breadcrumb_listItem__oW_Gf"]/a/text()')),
            "price": safe_xpath('//p[@class="media-0_headingSm__aysOm"]/text()').replace("£", "").strip(),
            "product_url": product_url,
            "description": safe_xpath('//p[@class="media-0_textSm__Q52Mz"]//text()', 1),
            "color": product_color[7] if len(product_color) > 7 else "",
            "size": ", ".join(safe_xpath_list('//span[@class="media-0_body__yf6Z_"]/text()')),
            "rating": safe_xpath('//span[contains(@class,"rating_score")]/text()'),
            "material": material_match.group(1) if material_match else "Not found",
            "care_instructions": care_match.group(1) if care_match else "Not found",
            "scraped_at": datetime.utcnow()
        }

        return product_data
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error for {product_url}: {req_err}")
    except Exception as e:
        logging.error(f"Unexpected error parsing {product_url}: {e}")
    return None


# Main
if __name__ == "__main__":
    logging.info("Starting parser (reading from MongoDB)...")

    product_urls = []
    for category_doc in categories_col.find():
        for sub in category_doc.get("subcategories", []):
            product_urls.extend(sub.get("products", []))

    logging.info(f"Found {len(product_urls)} product URLs in MongoDB")

    for i, url in enumerate(product_urls[:50], 1):  # limit first 10 for test
        logging.info(f"Parsing product {i}/{len(product_urls)}: {url}")
        product_data = parse_product(url)

        if product_data:
            products_detail_col.update_one(
                {"product_url": product_data["product_url"]},
                {"$set": product_data},
                upsert=True
            )
            logging.info(f"Saved product {i}: {product_data['product_name']}")
        else:
            logging.warning(f"Failed to parse product {i}")

    logging.info("Parsing complete! Data saved in 'products_detail' collection.")


