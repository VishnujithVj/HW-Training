import requests
from urllib.parse import urljoin

BASE_SITE = "https://www.jcpenney.com"

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'origin': 'https://www.jcpenney.com',
    'referer': 'https://www.jcpenney.com/',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'x-channel': 'desktop',
}

params = {
    'productGridView': 'medium',
    'id': 'cat100210006',
    'responseType': 'organic',
}
# ==========================================================
"""Fetch product data from JC Penney's search API"""
# ==========================================================

response = requests.get(
    'https://search-api.jcpenney.com/v1/search-service/g/women/tops',
    params=params,
    headers=headers,
)


if response.status_code == 200:
    data = response.json()
    products = data.get("organicZoneInfo", {}).get("products", [])
    print(f"Found {len(products)} products")
    

# ==========================================================================
# data extraction loop
# ==========================================================================
    for p in products:
        product_data = {
            "ppId": p.get("ppId"),
            "skuId": p.get("skuId"),
            "name": p.get("name"),
            "brand": p.get("brand"),
            "price_current_min": p.get("currentMin"),
            "price_current_max": p.get("currentMax"),
            "price_original_min": p.get("originalMin"),
            "price_original_max": p.get("originalMax"),
            "price_type": p.get("priceType"),
            "rating": p.get("averageRating"),
            "review_count": p.get("reviewCount"),
            "in_stock": not p.get("preOrder", False),
            "pdp_url": urljoin(BASE_SITE, p.get("pdpUrl", "")),
        }


# ===================================================================
# FINDINGS
# ===================================================================

"""
1. The script successfully fetches product data from JC Penney's search API.
2. Data extracted through product listing page API.
"""
