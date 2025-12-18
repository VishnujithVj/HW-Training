from curl_cffi import requests
from parsel import Selector
import json
from urllib.parse import urljoin

# ==============================================================
# CONFIG
# ==============================================================

BASE_URL = "https://staples-canada.myshopify.com"
COLLECTION_HANDLE = "printer-copy-paper-8454"

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
    "accept": "application/json",
}

# ==============================================================
# CATEGORY TEST (COLLECTION → PRODUCT URLS)
# ==============================================================

COLLECTION_API = (
    f"{BASE_URL}/collections/{COLLECTION_HANDLE}/products.json?limit=50"
)

resp = requests.get(
    COLLECTION_API,
    headers=HEADERS,
    impersonate="chrome",
    timeout=30
)


data = resp.json()
products = data.get("products", [])

PRODUCT_URLS = []

for p in products[:5]:  # sample only
    PRODUCT_URLS.append(
        urljoin(BASE_URL, f"/products/{p['handle']}")
    )

print("\nSample Product URLs:")
for url in PRODUCT_URLS:
    print(" -", url)

# ==============================================================
# PRODUCT PARSER (JSON-LD VALIDATION)
# ==============================================================

def parse_product(url: str):
    resp = requests.get(
        url,
        impersonate="chrome",
        timeout=30
    )

    sel = Selector(resp.text)

    json_ld = sel.xpath(
        '//script[@type="application/ld+json" and @id="product_details_json_ld"]/text()'
    ).get()

    if not json_ld:
        return None

    data = json.loads(json_ld)

    offers = data.get("offers", {}) or {}
    rating = data.get("aggregateRating", {}) or {}
    brand = data.get("brand", {}) or {}

    return {
        "product_id": data.get("sku"),
        "name": data.get("name"),
        "brand": brand.get("name"),
        "description": data.get("description"),
        "image": data.get("image"),
        "price": offers.get("price"),
        "currency": offers.get("priceCurrency"),
        "availability": offers.get("availability"),
        "offer_url": urljoin(BASE_URL, offers.get("url", "")),
        "rating_value": rating.get("ratingValue"),
        "review_count": rating.get("reviewCount"),
        "product_url": url,
    }



# ==============================================================
# FINDINGS
# ==============================================================

"""
FEASIBILITY FINDINGS

1. Category pages are accessible via website collection JSON endpoint.
2. Collection API reliably returns product IDs, titles, and handles.
3. Product detail pages expose stable JSON-LD blocks.
4. JSON-LD contains comprehensive product data (price, availability, ratings).
5. pagination limit is 250 products per request.

"""
