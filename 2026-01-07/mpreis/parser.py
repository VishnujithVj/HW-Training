from curl_cffi import requests
from parsel import Selector
from pymongo import MongoClient
import re
import time


# CONFIG
proxies = {
    "http": "http://pcofdppm:7uci0ruowenc@142.111.48.253:7030",
    "https": "http://pcofdppm:7uci0ruowenc@142.111.48.253:7030",
}

headers = {
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
}

# XPATH 
INGREDIENTS_XPATH = (
    '//div[contains(@class,"c3-detail-information__content-subitem")]'
    '[div[contains(@class,"c3-detail-information__content-block-title") and contains(text(),"Zutatenliste")]]'
    '//div[contains(@class,"c3-product-tab-content-items")]//text()'
)

ALLERGENS_XPATH = (
    '//div[contains(@class,"c3-detail-information__content-subitem")]'
    '[div[contains(@class,"c3-detail-information__content-block-title") and contains(text(),"Allergene")]]'
    '//div[contains(@class,"c3-product-tab-content-items")]//text()'
)

FEATURES_XPATH = (
    '//div[contains(@class,"c3-detail-information__content-subitem")]'
    '[div[contains(@class,"c3-detail-information__content-block-title") '
    'and (contains(text(),"Produktbezeichnung") '
    'or contains(text(),"Nettofüllmenge") '
    'or contains(text(),"Bruttogewicht") '
    'or contains(text(),"ID"))]]'
    '//div[contains(@class,"c3-product-tab-content-items")]//text()'
)

PRICE_CONTAINER_XPATH = (
    '//div[contains(@class,"c3-product__price--is-product-page")]'
    '//div[contains(@class,"c3-product__price")]'
)


# DB CONNECTION
client = MongoClient("mongodb://localhost:27017/")
db = client["mpreis_db"]
products_urls_col = db["products_url"]
product_data_col = db["product_data"]
failed_urls_col = db["failed_urls"]

product_data_col.create_index("url", unique=True)
failed_urls_col.create_index("url", unique=True)

# cleaning
def clean_text(text):
    if not text:
        return None
    return re.sub(r"\s+", " ", text).strip()

def clean_price(text):
    if not text:
        return None
    return re.sub(r"[^\d.]", "", text.replace(",", "."))

# PARSER 
urls = products_urls_col.find({})

for doc in urls:
    product_url = doc.get("url")
    if not product_url:
        continue

    print(f"Processing: {product_url}")

    try:
        response = requests.get(
            product_url,
            headers=headers,
            proxies=proxies,
            impersonate="chrome120",
            timeout=30,
        )
        selector = Selector(text=response.text)

        # Ingredients
        ingredients = clean_text(" ".join(selector.xpath(INGREDIENTS_XPATH).getall()))

        # Allergens 
        allergens = clean_text(" ".join(selector.xpath(ALLERGENS_XPATH).getall()))

        # Product features 
        features = clean_text(" ".join(selector.xpath(FEATURES_XPATH).getall()))

        # Price & Price per Unit 
        price_container = selector.xpath(PRICE_CONTAINER_XPATH)
        price_texts = [t.strip() for t in price_container.xpath(".//text()").getall() if t.strip()]

        price = None
        price_per_unit = None

        for txt in price_texts:
            if re.search(r"\d+,\d+", txt) and "€" not in txt:
                price = clean_price(txt)
            if "€" in txt and "/" in txt:
                price_per_unit = clean_text(txt)

        # items
        item = {
            "url": product_url,
            "brand": doc.get("brand"),
            "category_url": doc.get("category_url"),
            "product_name": doc.get("product_name"),
            "size": doc.get("size"),
            "price": price,
            "price_per_unit": price_per_unit,
            "Ingredients": ingredients,
            "Allergens": allergens,
            "Product_features": features,
        }

        product_data_col.update_one(
            {"url": product_url},
            {"$set": item},
            upsert=True
        )

        time.sleep(1)

    except Exception as e:
        failed_urls_col.update_one(
            {"url": product_url},
            {"$set": {"url": product_url, "error": str(e)}},
            upsert=True
        )
        continue
