from curl_cffi import requests
from parsel import Selector
from urllib.parse import urljoin
from pymongo import MongoClient
import re
import time

# ======================
# CONFIG
# ======================
BASE_URL = "https://www.mpreis.at"
CATEGORY_URL = "https://www.mpreis.at/shop/c/lebensmittel/tiefkuehl-42512882"

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

# ======================
# XPATH CONFIG
# ======================
PRODUCT_CARD_XPATH = '//a[contains(@class,"c3-product-grid__item")]'
URL_XPATH = "./@href"
BRAND_XPATH = './/span[contains(@class,"c3-product__producer")]/text()'
NAME_XPATH = './/span[contains(@class,"c3-product__name")]/text()'
SIZE_XPATH = './/div[contains(@class,"c3-product__weight-info-text")]/text()'
PRICE_XPATH = './/div[contains(@class,"c3-product__price")]/div[@aria-hidden="true"]/text()'

# ======================
# DB
# ======================
client = MongoClient("mongodb://localhost:27017/")
db = client["mpreis_db"]
collection = db["products_url"]
collection.create_index("url", unique=True)

# ======================
# HELPERS
# ======================
def clean_price(text):
    if not text:
        return None
    m = re.search(r"\d+[.,]\d+", text)
    return float(m.group().replace(",", ".")) if m else None

# ======================
# CRAWLER
# ======================
page = 1
total_saved = 0

while True:
    page_url = f"{CATEGORY_URL}?currentPage={page}&step=0"
    print(f"Fetching page {page}")

    response = requests.get(
        page_url,
        headers=headers,
        proxies=proxies,
        impersonate="chrome120",
        timeout=30,
    )

    selector = Selector(text=response.text)

    products = selector.xpath(PRODUCT_CARD_XPATH)
    if not products:
        print("No more products found. Stop.")
        break

    for p in products:
        rel_url = p.xpath(URL_XPATH).get()
        product_url = urljoin(BASE_URL, rel_url) if rel_url else None

        brand = p.xpath(BRAND_XPATH).get(default="").strip() or None
        name = p.xpath(NAME_XPATH).get(default="").strip() or None
        size = p.xpath(SIZE_XPATH).get(default="").strip() or None

        selling_price = clean_price(
            " ".join(p.xpath(PRICE_XPATH).getall())
        )

        item = {
            "url": product_url,
            "product_name": name,
            "brand": brand,
            "size": size,
            "price": selling_price,
            "category_url": CATEGORY_URL,
            "page": page,
        }

        if product_url:
            collection.update_one(
                {"url": product_url},
                {"$set": item},
                upsert=True
            )
            total_saved += 1

    page += 1
    time.sleep(1)

