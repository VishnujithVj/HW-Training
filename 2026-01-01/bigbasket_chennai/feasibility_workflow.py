import re
from curl_cffi import requests
from urllib.parse import urljoin
from pymongo import MongoClient


BASE_URL = "https://www.bigbasket.com"
API_URL = f"{BASE_URL}/listing-svc/v2/products"


# CATEGORIES
CATEGORIES = {
    "tea": {"type": "pc", "slug": "tea"},
    "coffee": {"type": "pc", "slug": "coffee"},
}


# db and collection
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "bigbasket_db_2"
PRODUCT_COLLECTION = "products_new"
URL_COLLECTION = "product_urls"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "referer": BASE_URL,
    "x-channel": "BB-WEB",
    "x-entry-context": "bbnow",
    "x-entry-context-id": "10",
}


class BigBasketCrawler:

    def __init__(self):
        self.session = requests.Session(impersonate="chrome120")
        self.session.get(BASE_URL, headers=HEADERS, timeout=30)

        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.product_col = self.db[PRODUCT_COLLECTION]
        self.url_col = self.db[URL_COLLECTION]


    def start(self):
        for category_name, category in CATEGORIES.items():
            page = 1
            total_pages = 1

            while page <= total_pages:
                data = self.fetch_page(category, page)

                tab = data.get("tabs", [{}])[0]
                info = tab.get("product_info", {})
                products = info.get("products", [])
                total_pages = info.get("number_of_pages", 1)

                for product in products:
                    self.parse_and_save(product, tab, category_name)

                page += 1

        self.client.close()

 
    def fetch_page(self, category, page):
        r = self.session.get(
            API_URL,
            params={
                "type": category["type"],
                "slug": category["slug"],
                "page": page,
            },
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()


    def build_breadcrumbs(self, tab, p):
        crumbs = ["Home"]
        for c in tab.get("bread_crumbs", []):
            crumbs.append(c.get("name", "").lower())

        llc = (p.get("category") or {}).get("llc_name")
        if llc:
            crumbs.append(llc.lower())
        return " / ".join(crumbs)


    def extract_pack_size(self, text):
        m = re.search(r"(\d+(\.\d+)?\s?(kg|g|ml|l))", text, re.I)
        return m.group(0) if m else None

    # parser and save
    def parse_and_save(self, p, tab, category_name):
        brand = (p.get("brand") or {}).get("name", "").strip()
        desc = p.get("desc", "").strip()
        pack_size = self.extract_pack_size(desc) or p.get("w")

        product_name = f"{brand} {desc}".strip()
        if pack_size:
            product_name = f"{product_name}, {pack_size}"

        parent_sku = p.get("id")
        parent_url = urljoin(BASE_URL, p.get("absolute_url", ""))


        # VARIANT URL LIST
        variants = []
        for c in p.get("children", []):
            variants.append({
                "variant_sku": c.get("id"),
                "variant_url": urljoin(BASE_URL, c.get("absolute_url", "")),
            })


        self.url_col.update_one(
            {"parent_sku": parent_sku},
            {
                "$set": {
                    "parent_sku": parent_sku,
                    "parent_url": parent_url,
                    "variants": variants,
                }
            },
            upsert=True,
        )

        pricing = p.get("pricing", {})
        prim = pricing.get("prim_price", {})
        discount = pricing.get("discount", {})

        # Save items
        self.product_col.update_one(
            {"sku_id": parent_sku},
            {
                "$set": {
                    "sku_id": parent_sku,
                    "product_name": product_name,
                    "parent_url": parent_url,
                    "variant_urls": variants,
                    "mrp": discount.get("mrp"),
                    "selling_price": prim.get("sp"),
                    "rating": (p.get("rating_info") or {}).get("avg_rating"),
                    "rating_count": (p.get("rating_info") or {}).get("rating_count"),
                    "sold_info": p.get("number_of_skus_sold"),
                    "breadcrumbs": self.build_breadcrumbs(tab, p),
                    "top_category": category_name,
                    "availability": (p.get("availability") or {}).get("avail_status"),
                }
            },
            upsert=True,
        )



# ==============================================
# finding
# ==============================================
"""
1. site have active bot detection mechanism(cloudflare)
"""
