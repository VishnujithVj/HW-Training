from curl_cffi import requests
from parsel import Selector
from pymongo import MongoClient, errors
import json
import re
import time


# INIT
client = MongoClient("mongodb://localhost:27017/")
db = client["nykka_db"]

urls_collection = db["product_urls"]
data_collection = db["product_data"]
data_collection.create_index("product_url", unique=True)

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "accept-language": "en-US,en;q=0.9",
}

cookies = {
    "countryCode": "IN",
    "storeId": "nykaa",
}

# PARSER
def parse_nykaa_product(product_url):
    try:
        response = requests.get(
            product_url,
            headers=headers,
            cookies=cookies,
            impersonate="chrome",
            timeout=30
        )
    except Exception as e:
        print("Request error:", e)
        return None

    selector = Selector(response.text)


    # Product data
    product_data = {}
    script_text = selector.xpath('//script[contains(text(),"window.dataLayer")]/text()').get()
    if script_text:
        match = re.search(r'window\.dataLayer\s*=\s*(\[\{.*?\}\]);', script_text, re.S)
        if match:
            try:
                data_layer = json.loads(match.group(1))
                product_data = data_layer[0].get("product", {})
            except:
                pass


    # DESCRIPTION / INGREDIENTS / HOW TO USE
    def clean_html(text):
        if not text:
            return None
        text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    description = None
    ingredients = None
    how_to_use = None

    preloaded_script = selector.xpath(
        '//script[contains(text(),"window.__PRELOADED_STATE__")]/text()'
    ).get()

    if preloaded_script:
        match = re.search(
            r'window\.__PRELOADED_STATE__\s*=\s*({.*})\s*$',
            preloaded_script.strip(),
            re.S
        )
        if match:
            try:
                preloaded_state = json.loads(match.group(1))
                product = (
                    preloaded_state
                        .get("productPage", {})
                        .get("product", {})
                )

                description = clean_html(product.get("description"))
                ingredients = clean_html(product.get("ingredients"))
                how_to_use = clean_html(product.get("howToUse"))

            except Exception as e:
                print("PRELOADED_STATE parse error:", e)

    # Images
    image_urls = selector.xpath(
        '//div[contains(@class,"slide-view-container")]//img/@src'
    ).getall()

    main_image = selector.xpath(
        '//div[contains(@class,"productSelectedImage")]//img/@src'
    ).get()

    if main_image and main_image not in image_urls:
        image_urls.append(main_image)

    # Breadcrumbs 
    crumbs = selector.xpath(
        '//ul[contains(@class,"css-1uxnb1o")]/li/a/text()'
    ).getall()

    crumbs = [c.strip() for c in crumbs if c.strip()]
    breadcrumbs = " > ".join(["Home"] + crumbs)


    # data item
    return {
        "product_id": product_data.get("id"),
        "sku": product_data.get("sku"),
        "brand_name": product_data.get("brandName"),
        "package_size": product_data.get("packSize"),
        "discount": product_data.get("discount"),
        "rating_count": product_data.get("ratingCount"),
        "review_count": product_data.get("reviewCount"),
        "images": image_urls,
        "breadcrumbs": breadcrumbs,
        "description": description,
        "ingredients": ingredients,
        "how_to_use": how_to_use,
    }

#start
inserted_count = 0
skipped_count = 0

for record in urls_collection.find():
    product_url = record.get("product_url")
    category_url = record.get("category_url")

    if not product_url:
        continue

    print(f"\nParsing product: {product_url}")

    parsed_data = parse_nykaa_product(product_url)
    if not parsed_data:
        print("Failed to parse:", product_url)
        continue

    item = {
        "category_url": category_url,
        "product_url": product_url,
        "product_name": record.get("product_name"),
        "selling_price": record.get("selling_price"),
        "regular_price": record.get("regular_price"),
        "promotion_description": record.get("promotion_description"),
    }
    item.update(parsed_data)

    try:
        data_collection.insert_one(item)
        inserted_count += 1
        print("Inserted:", product_url)
    except errors.DuplicateKeyError:
        skipped_count += 1
        print("Duplicate skipped:", product_url)
    except Exception as e:
        print("Mongo error:", e)

    time.sleep(1)
