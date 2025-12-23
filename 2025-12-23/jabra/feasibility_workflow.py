from curl_cffi import requests
from parsel import Selector
from urllib.parse import urljoin
import json

URL = "https://www.jabra.com/"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "upgrade-insecure-requests": "1",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
}

session = requests.Session()
response = session.get(URL, headers=HEADERS, impersonate="chrome", timeout=30)
response.raise_for_status()

selector = Selector(text=response.text)
# ===================================
# category_test
# ===================================

links = selector.xpath(
    '//ul[@aria-label="Our products"]//a'
)

results = []

for a in links:
    href = a.xpath('./@href').get()
    name = a.xpath('normalize-space(text())').get()

    if not href or not name:
        continue

    results.append({
        "category": name,
        "slug": href.rstrip("/").split("/")[-1],
        "href": urljoin(URL, href),
    })

# =================================
# crawler_test.py
# =================================

BASE_URL = "https://sfcc-prod-api.jabra.com/s/jabra-amer/dw/shop/v24_1/product_search"

PARAMS = {
    "refine_1": "c_countryProductState=3",
    "expand": "prices",
    "locale": "en-US",
    "refine_2": "orderable_only=true",
    "refine_3": "c_countryOnlineFlag=1",
    "refine_4": "c_portfolio=Jabra",
    "refine_5": "c_productType=1|5|6|7|9",
    "count": 8,
    "start": 0,
}


JABRA_PRODUCT_URL_TEMPLATE = "https://www.jabra.com/business/buy?sku={sku}"


def crawl_all_products():
    all_products = []
    start = 0
    total = None

    session = requests.Session()
    session.headers.update(HEADERS)

    while True:
        PARAMS["start"] = start

        response = session.get(
            BASE_URL,
            params=PARAMS,
            impersonate="chrome",
            timeout=30,
        )

        if response.status_code != 200:
            break

        data = response.json()

        if total is None:
            total = data.get("total", 0)

        hits = data.get("hits", [])
        if not hits:
            break

        for hit in hits:
            product_id = hit.get("product_id")

            all_products.append({
                "product_id": product_id,
                "product_name": hit.get("product_name"),
                "price": hit.get("price"),
                "price_per_unit": hit.get("price_per_unit"),
                "currency": hit.get("currency"),
                "product_url": JABRA_PRODUCT_URL_TEMPLATE.format(sku=product_id),
            })

        start += PARAMS["count"]

        if start >= total:
            break

    return all_products
# ==============================
# findings 
# ==============================

"""
1.
   """