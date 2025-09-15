import re
import time
from urllib.parse import urljoin
from curl_cffi import requests
from parsel import Selector
from pymongo import MongoClient

# --- Configurations ---
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "carbon38_curl"
URL_COLLECTION = "product_urls"        # input URLs
DETAILS_COLLECTION = "product_details" # output details

# --- MongoDB Setup ---
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
urls_collection = db[URL_COLLECTION]
details_collection = db[DETAILS_COLLECTION]

# --- Headers ---
HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "accept-language": "en-US,en;q=0.9",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


def parse_product_page(url: str):
    """Fetch and parse product details using curl_cffi + parsel."""
    try:
        resp = requests.get(url, headers=HEADERS, impersonate="chrome110", timeout=60)
        if resp.status_code != 200:
            print(f"❌ Failed {url}: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Request error for {url}: {e}")
        return None

    sel = Selector(resp.text)

    try:
        # --- Product name ---
        product_name = sel.xpath('//h1[contains(@class,"ProductMeta__Title")]/text()').get()

        # --- Brand ---
        brand = sel.xpath('//h2[contains(@class,"ProductMeta__Vendor")]//a/text()').get()

        # --- Price ---
        price = sel.xpath('//span[contains(@class,"ProductMeta__Price")]/text()').get()

        # --- Colour ---
        colour = sel.xpath('//span[contains(@class,"ProductForm__SelectedValue")]/text()').get()

        # --- Sizes (list) ---
        sizes = sel.xpath('//input[contains(@class,"SizeSwatch__Radio")]/@value').getall()

        # --- Images ---
        images = sel.xpath('//img[contains(@class,"Product__SlideImage")]/@src').getall()
        images = [
            img if img.startswith("http") else "https:" + img
            for img in images
            if img
        ]

        # --- FAQ Section (Description) ---
        raw_html = sel.xpath('//div[contains(@class,"Faq__AnswerWrapper")]//p').get()
        description = ""
        if raw_html:
            description = re.sub(r'<br\s*/?>', '\n', raw_html)
            description = re.sub(r'<[^>]+>', '', description).strip()

        if not product_name:
            print(f" Missing product name for {url}")
            return None

        details = {
            "product_url": url,
            "product_name": product_name.strip() if product_name else "",
            "brand": brand.strip() if brand else "",
            "price": price.strip() if price else "",
            "colour": colour.strip() if colour else "",
            "sizes": [s.strip() for s in sizes],
            "images": images,
            "description": description,
        }

        return details

    except Exception as e:
        print(f" Error parsing {url}: {e}")
        return None


def main():
    urls = urls_collection.find({}, {"url": 1, "_id": 0})
    count = 0

    for entry in urls:
        url = entry["url"]
        print(f"🔎 Scraping product: {url}")

        details = parse_product_page(url)
        if details:
            details_collection.update_one(
                {"product_url": details["product_url"]},
                {"$set": details},
                upsert=True
            )
            count += 1
            print(f" ✅ Saved product: {details['product_name']}")
        time.sleep(2)  # polite delay

    print(f"\n Finished scraping {count} products.")
    client.close()


if __name__ == "__main__":
    main()
