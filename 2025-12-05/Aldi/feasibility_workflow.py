import requests
import json
from pymongo import MongoClient

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
}

#------------------------------CATEGORY_CRAWLER---------------------#

"""API: Returns category → subcategory hierarchy"""
category_tree_api = "https://api.aldi.co.uk/v2/product-category-tree?serviceType=walk-in&servicePoint=C092"

category_response = requests.get(category_tree_api, headers=HEADERS)
category_json = category_response.json()

"""API: Fetch products by category key"""
product_list_api = "https://api.aldi.co.uk/v3/product-search"

params = {
    "currency": "GBP",
    "serviceType": "walk-in",
    "servicePoint": "C092",
    "limit": 30,
    "offset": 0,
    "categoryKey": "",     
}

listing_response = requests.get(product_list_api, params=params, headers=HEADERS)
listing_json = listing_response.json()


# Each product contains:
# {
#   "sku": "000000000000384321",
#   "name": "British Chicken",
#   "urlSlugText": "british-chicken"
# }

# Sample constructed product URL:
# https://www.aldi.co.uk/product/british-chicken-000000000000384321

#--------------------CRAWLER ------------------------------#

"""PDP API for complete product data"""
sku = "000000000000384321"
pdp_api = f"https://api.aldi.co.uk/v2/products/{sku}?servicePoint=C092&serviceType=walk-in"

pdp_response = requests.get(pdp_api, headers=HEADERS)
pdp_json = pdp_response.json()


#--------------------PARSER AND PRODUCT DETAIL ------------------------------#
"""DATA FIELDS"""
product_id = pdp_json.get("data", {}).get("sku")
product_name = pdp_json.get("data", {}).get("name")
brand_name = pdp_json.get("data", {}).get("brandName")
selling_size = pdp_json.get("data", {}).get("sellingSize")
price_block = pdp_json.get("data", {}).get("price", {})
price = price_block.get("amountRelevantDisplay")
comparison_price = price_block.get("comparisonDisplay")
categories = pdp_json.get("data", {}).get("categories", [])

"""breadcrumbs → Home > Fresh Food > Poultry"""
breadcrumb_list = ["Home"] + [c.get("name") for c in categories]
breadcrumbs = " > ".join(breadcrumb_list)



#-----------------------------FINDINGS--------------------------#

# Category data available through API v2
# PLP / product listings available via API v3
# PDP fully available via API v2
# Pricing, comparison price, pack size, brand available
# Breadcrumbs fully returned in PDP API

