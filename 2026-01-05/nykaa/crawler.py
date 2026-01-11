from curl_cffi import requests
from parsel import Selector
from urllib.parse import urljoin
from pymongo import MongoClient, errors
import time


# INIT
BASE_URL = "https://www.nykaa.com"
MAX_PAGES = 5   

CATEGORY_URLS = [
    "https://www.nykaa.com/makeup/face/c/13?ptype=lst&id=13&root=nav_2&dir=desc&order=popularity",
    "https://www.nykaa.com/skin/moisturizers/c/8393",
    "https://www.nykaa.com/hair-care/hair/c/25?root=nav_2&dir=desc&order=popularity",
    "https://www.nykaa.com/bath-body/bath-and-shower/c/35?ptype=lst&id=35&root=nav_2&dir=desc&order=popularity",
]

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "accept-language": "en-US,en;q=0.9",
}

cookies = {
    "countryCode": "IN",
    "storeId": "nykaa",
}

client = MongoClient("mongodb://localhost:27017/")
db = client["nykka_db"]
collection = db["product_urls"]

collection.create_index("product_url", unique=True)

inserted_count = 0
skipped_count = 0

# START
for category_url in CATEGORY_URLS:
    print(f"\n=== CATEGORY ===\n{category_url}")
    page = 1

    while page <= MAX_PAGES:
        print(f"Fetching page {page}")

        page_url = category_url + f"&page_no={page}"

        response = requests.get(
            page_url,
            headers=headers,
            cookies=cookies,
            impersonate="chrome"
        )

        if response.status_code != 200:
            print("Request failed:", response.status_code)
            break

        selector = Selector(response.text)
        products = selector.xpath('//a[contains(@class,"css-qlopj4")]')

        if not products:
            print("No more products")
            break

        for product in products:
            product_url = urljoin(BASE_URL, product.xpath('./@href').get())

            item = {
                "category_url": category_url,
                "product_url": product_url,
                "product_name": product.xpath('.//div[contains(@class,"css-xrzmfa")]/text()').get(),
                "selling_price": product.xpath('.//span[contains(@class,"css-111z9ua")]/text()').get(),
                "regular_price": product.xpath('.//span[contains(@class,"css-17x46n5")]/span/text()').get(),
                "promotion_description": product.xpath('.//span[contains(@class,"css-cjd9an")]/text()').get(),
            }

            try:
                collection.insert_one(item)
                inserted_count += 1
                print("Inserted item")
            except errors.DuplicateKeyError:
                skipped_count += 1
                print("Duplicate skipped")
            except Exception as e:
                print("Mongo error:", e)

        page += 1
        time.sleep(1)

