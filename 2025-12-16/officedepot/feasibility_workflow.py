from curl_cffi import requests
from parsel import Selector
import json
from urllib.parse import urljoin

# ==============================================================
# 1. CONFIG
# ==============================================================

BASE_URL = "https://www.officedepot.com"

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ==============================================================
# 2. CATEGORY TEST (ENTRY POINT)
# ==============================================================

CATEGORY_URL = "https://www.officedepot.com/b/office-supplies/N-1676"

resp = requests.get(CATEGORY_URL, headers=HEADERS, impersonate="chrome", timeout=20)
print("Category Page Status:", resp.status_code)

sel = Selector(resp.text)

product_cards = sel.xpath('//a[@class="od-product-card-image"]')
print("Products Found:", len(product_cards))

PRODUCT_URLS = []

for card in product_cards[:5]: 
    href = card.xpath('./@href').get()
    title = card.xpath('./@title').get()

    if href:
        PRODUCT_URLS.append(urljoin(BASE_URL, href))

print("Sample Product URLs:")
for url in PRODUCT_URLS:
    print(" -", url)

# ==============================================================
# 3. PRODUCT PARSER (JSON-LD VALIDATION)
# ==============================================================

def parse_product(url):
    resp = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=20)
    print("\nProduct Status:", resp.status_code, "|", url)

    sel = Selector(resp.text)

    ld_json = sel.xpath('//script[@type="application/ld+json"]/text()').get()
    if not ld_json:
        print("❌ JSON-LD not found")
        return None

    data = json.loads(ld_json)

    # -------------------------
    # FIELDS
    # -------------------------
    sku = data.get("sku")
    name = data.get("name")
    description = data.get("description")
    brand = data.get("brand")

    offers = data.get("offers", {}) or {}
    price = offers.get("price")
    currency = offers.get("priceCurrency")

    category = ""
    for crumb in data.get("breadcrumbs", []):
        if crumb.get("type") == "category":
            category = crumb.get("name")
            break

    image = ""
    if isinstance(data.get("image"), dict):
        image = data["image"].get("contentUrl")

    return {
        "sku": sku,
        "product_title": name,
        "category": category,
        "price": price,
        "currency": currency,
        "brand": brand,
        "description": description,
        "image": image,
        "product_url": url,
    }

# ==============================================================
# 4. RUN FEASIBILITY TEST
# ==============================================================

for url in PRODUCT_URLS:
    details = parse_product(url)
    print(json.dumps(details, indent=2, ensure_ascii=False))

# ==============================================================
# 5. FINDINGS 
# ==============================================================

"""
1. Category pages reliably expose product URLs.
2. Product detail pages contain stable JSON-LD blocks.
3. SKU, price, currency, brand, category, and images are available via JSON-LD.
4. No additional requests are required for reviews and ratings.

"""
