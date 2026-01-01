from curl_cffi import requests
import time
import re
import random

# ======================
# CONFIG
# ======================
API_URL = "https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v2"

CATEGORY_ID = "5xsy9"
CATEGORY_PAGE = "/c/snacks-grocery/-/N-5xsy9"

PAGE_SIZE = 24
OFFSET = 0

SLEEP_RANGE = (1.1, 2.2)
OUTPUT_JSON = "target_products.json"
VISITOR_ID = "019B729332920201AC1F61A30AC14C1E"


# ======================
# HEADERS
# ======================
HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://www.target.com",
    "referer": f"https://www.target.com{CATEGORY_PAGE}",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
}

# ======================
# BASE PARAMS
# ======================
BASE_PARAMS = {
    "key": "9f36aeafbe60771e321a7cc95a78140772ab3e96",
    "category": CATEGORY_ID,
    "count": PAGE_SIZE,
    "platform": "desktop",
    "pricing_store_id": "1771",
    "store_ids": "1771,1768,1113,3374,1792",
    "scheduled_delivery_store_id": "1771",
    "zip": "52404",
    "visitor_id": VISITOR_ID,
    "channel": "WEB",

    "default_purchasability_filter": "true",
    "include_sponsored": "true",
    "include_review_summarization": "true",
    "spellcheck": "true",
    "include_dmc_dmr": "true",

    # REQUIRED — prevents HTTP 400
    "page": CATEGORY_PAGE,
}

# ======================
# STORAGE
# ======================
all_products = []
seen_tcins = set()


# ======================
# CRAWLING LOOP
# ======================
while True:
    """Fetch products using offset pagination"""
    params = BASE_PARAMS.copy()
    params["offset"] = OFFSET  

    resp = requests.get(
        API_URL,
        params=params,
        headers=HEADERS,
        impersonate="chrome120",
        timeout=60,
    )

    """Soft block handling"""
    if resp.status_code in (403, 429):
        time.sleep(random.uniform(10, 20))
        continue

    if resp.status_code != 200:
        print(f"HTTP {resp.status_code}")
        break

    data = resp.json()

    products = (
        data.get("data", {})
            .get("search", {})
            .get("products", [])
    )

    if not products:
        print("No more products")
        break

    for p in products:
        tcin = p.get("tcin")
        if not tcin or tcin in seen_tcins:
            continue

        seen_tcins.add(tcin)

        enrichment = p.get("enrichment", {})
        description = p.get("product_description", {})

        # Clean bullet descriptions
        bullets = []
        for d in description.get("bullet_descriptions", []):
            if d:
                bullets.append(re.sub(r"<[^>]+>", "", d).strip())

        # Images
        images = []
        primary_img = enrichment.get("image_info", {}).get("primary_image_url")
        if primary_img:
            images.append(primary_img)

        images.extend(
            enrichment.get("images", {}).get("alternate_image_urls", [])
        )

        product = {
            "product_id": tcin,
            "title": description.get("title"),
            "brand": p.get("primary_brand", {}).get("name"),
            "buy_url": enrichment.get("buy_url"),
            "images": images,
            "description": bullets,
            "price": (
                p.get("price", {}).get("formatted_current_price")
                or p.get("price", {}).get("formatted_unit_price")
            ),
            "sponsored": p.get("is_sponsored_sku", False),
        }

        all_products.append(product)

    OFFSET += PAGE_SIZE
    time.sleep(random.uniform(*SLEEP_RANGE))


"""
======================
FINDINGS
======================

1. Target PLP API uses 'offset' (Nao) for pagination.
2. Site has heavy blocking mechanisms (Cloudflare).
"""
