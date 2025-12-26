
import json
import re
import time
import random
import csv
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from curl_cffi import requests

# =====================================================
# CONFIG
# =====================================================
BASE_URL = "https://www.bigbasket.com"
LISTING_API = f"{BASE_URL}/listing-svc/v2/products"

CATEGORIES = {
    "tea": {"type": "pc", "slug": "tea"},
    "coffee": {"type": "pc", "slug": "coffee"},
}

OUTPUT_JSON = "bigbasket.json"
OUTPUT_JSONL = "bigbasket_products.jsonl"
OUTPUT_CSV = "bigbasket_products.csv"

# =====================================================
# USER AGENTS
# =====================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Firefox/142.0",
]

# =====================================================
# BASE HEADERS & COOKIES
# =====================================================
BASE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "x-channel": "BB-WEB",
    "x-entry-context": "bbnow",
    "x-entry-context-id": "10",
    "user-agent": random.choice(USER_AGENTS),
    "referer": BASE_URL,
}

BASE_COOKIES = {
    "_bb_locSrc": "default",
    "_bb_pin_code": "400054",
    "x-channel": "web",
}

# =====================================================
# SESSION (curl_cffi)
# =====================================================
session = requests.Session(impersonate="chrome120")
session.get(BASE_URL, headers=BASE_HEADERS, timeout=30) 

# =====================================================
# -------------------- CRAWLER -------------------------
# =====================================================
def fetch_listing_page(category, page):
    params = {
        "type": category["type"],
        "slug": category["slug"],
        "page": page,
    }

    r = session.get(
        LISTING_API,
        params=params,
        headers=BASE_HEADERS,
        cookies=BASE_COOKIES,
        timeout=30,
    )

    if r.status_code != 200:
        raise Exception(f"BLOCKED | Page {page} | Status {r.status_code}")

    return r.json()


def run_crawler():
    """
    Collects all Tea & Coffee products via listing API
    """
    final_data = {}

    for name, category in CATEGORIES.items():

        page = 1
        total_pages = 1
        total_count = 0
        products_all = []

        while page <= total_pages:
            data = fetch_listing_page(category, page)

            info = data["tabs"][0]["product_info"]
            products = info.get("products", [])

            total_pages = info.get("number_of_pages", 1)
            total_count = info.get("total_count", 0)

            print(f"  Page {page}/{total_pages} → {len(products)} items")

            for p in products:
                pricing = p.get("pricing", {}).get("discount", {})
                prim = pricing.get("prim_price", {})

                products_all.append({
                    "id": p.get("id"),
                    "name": p.get("desc"),
                    "brand": (p.get("brand") or {}).get("name"),
                    "weight": p.get("w"),
                    "unit": p.get("unit"),
                    "usp": p.get("usp"),
                    "selling_price": prim.get("sp"),
                    "mrp": pricing.get("mrp"),
                    "product_url": urljoin(BASE_URL, p.get("absolute_url", "")),
                })

            page += 1
            time.sleep(1)

        final_data[name] = {
            "category": name,
            "slug": category["slug"],
            "total_products": total_count,
            "pages": total_pages,
            "products": products_all,
        }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)


    return final_data

# =====================================================
# -------------------- PARSER --------------------------
# =====================================================
def fetch_html(url, retries=3):
    for i in range(retries):
            headers = {
                "user-agent": random.choice(USER_AGENTS),
                "accept": "text/html,application/xhtml+xml",
            }

            s = requests.Session(impersonate="chrome")
            r = s.get(url, headers=headers, cookies=BASE_COOKIES, timeout=30)

            if r.status_code == 403:
                time.sleep(2 * (i + 1))
                continue

            r.raise_for_status()
            return r.text

def parse_pdp(url, meta):
    html = fetch_html(url)
    if not html:
        return None

    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not m:
        return None

    data = json.loads(m.group(1))
    product = data["props"]["pageProps"]["productDetails"]
    product = product["children"][0] if product.get("children") else product

    breadcrumb = [b["name"] for b in product.get("breadcrumb", [])]

    images = product.get("images", [])


    return {
        "unique_id": product.get("id"),
        "retailer_name": "BigBasket",
        "extraction_date": datetime.now().strftime("%Y-%m-%d"),
        "product_name": f"{meta.get('brand')} {meta.get('name')}, {meta.get('weight')}",
        "brand": meta.get("brand"),
        "regular_price": meta.get("mrp"),
        "selling_price": meta.get("selling_price"),
        "currency": "INR",
        "pdp_url": url,
        "images": images,
        "beadcrumb": " > ".join(breadcrumb),
    }


# =====================================================
# -------------------- FINDINGS ------------------------
# =====================================================

"""
FINDINGS
--------
1. Categories: Tea & Coffee only
2. Pagination: is infinate scroll
3. Blocking: Occasional 403 on PDP → resolved via UA rotation
4. Coverage: All products accessible via listing API
"""
