from curl_cffi import requests
from parsel import Selector
import json

# ==============================================================
# 1. CONFIG
# ==============================================================

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}

# ==============================================================
# 2. INPUT SEARCH URL
# ==============================================================

SEARCH_URL = "https://www.elcorteingles.es/search-nwx/1/?s=8470001901200&stype=text_box"

search_resp = requests.get(SEARCH_URL, headers=HEADERS, impersonate="chrome", timeout=20)
print("Search Page Status:", search_resp.status_code)

sel = Selector(text=search_resp.text)

# Extract product items
product_blocks = sel.xpath('//li[contains(@class,"products_list-item")]')
print("Products Found on Search:", len(product_blocks))

PRODUCT_URLS = []

for product in product_blocks:
    href = product.xpath('.//a[contains(@class,"product_preview-title")]/@href').get()
    if href:
        PRODUCT_URLS.append("https://www.elcorteingles.es" + href)


# ==============================================================
# 3. PRODUCT PARSER FUNCTION
# ==============================================================

def parse_product(url):
    resp = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=20)
    sel = Selector(text=resp.text)

    # ---------------------------
    # TEXT FIELDS
    # ---------------------------

    brand = sel.xpath('//div[contains(@class,"product_detail-brand")]//a/text()').get()
    title = sel.xpath('//h1[@id="product_detail_title"]//text()').get()
    description = sel.xpath('//div[@class="product_detail-description"]//p/text()').get()

    # Clean
    brand = brand.strip() if brand else None
    title = title.strip() if title else None
    description = description.strip() if description else None

    # ---------------------------
    # PRODUCT DATA SECTION (Model / Reference / EAN)
    # ---------------------------
    model = sel.xpath('//div[contains(text(),"Modelo")]/text()').get()
    reference = sel.xpath('//div[contains(text(),"Referencia")]/text()').get()
    ean = sel.xpath('//div[contains(text(),"EAN")]/text()').get()

    if model:     model = model.replace("Modelo:", "").strip()
    if reference: reference = reference.replace("Referencia:", "").strip()
    if ean:       ean = ean.replace("EAN:", "").strip()

    # ---------------------------
    # IMAGES
    # ---------------------------
    image = sel.xpath('//picture/source[1]/@srcset').get()
    if not image:
        image = sel.xpath('//picture/img/@src').get()

    # ---------------------------
    # PRICE (JSON-LD extraction)
    # ---------------------------

    ld_json_scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()

    json_price = None
    for block in ld_json_scripts:
        try:
            data = json.loads(block.strip())
            if isinstance(data, dict) and data.get("@type") == "Product":
                if "offers" in data and "price" in data["offers"]:
                    json_price = data["offers"]["price"]
                    break
        except:
            pass

    return {
        "url": url,
        "brand": brand,
        "title": title,
        "description": description,
        "model": model,
        "reference": reference,
        "ean": ean,
        "image": image,
        "price_from_json": json_price
    }


# ==============================================================
# RUN PARSER
# ==============================================================

for url in PRODUCT_URLS:
    details = parse_product(url)
    print(json.dumps(details, ensure_ascii=False, indent=2))


# ==============================================================
# 5. FINDINGS
# ==============================================================

# 1. Based on the current inputs, most records return an exact match when searched using the EAN Master.

# 2. If both the EAN Master and CNK Belux return no results, searching with the product’s general name provides partial matches, though name‑based matching is often unpredictable.

# 3. Searching with EAN Master and CNK Belux inputs sometimes returns no results.

# 4. A single input may correspond to multiple products.

# 5. Name details can be extracted directly from PLP pages without additional requests, but retrieving price information requires additional requests.