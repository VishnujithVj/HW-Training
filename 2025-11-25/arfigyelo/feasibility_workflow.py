import requests
import json
import time

# ================================================
# categories crawler - test
# ================================================

url = "https://arfigyelo.gvh.hu/api/categories"
base = "https://arfigyelo.gvh.hu/k/"
result = []

r = requests.get(url, timeout=15)
data = r.json()

categories = data.get("categories", [])
for cat in categories:
    node = {
        "id": cat.get("id"),
        "name": cat.get("name"),
        "path": cat.get("path"),
        "url": base + cat.get("path", ""),
        "subcategories": []
    }
    
    children = cat.get("categoryNodes", [])
    for sub in children:
        node["subcategories"].append({
            "id": sub.get("id"),
            "name": sub.get("name"),
            "path": sub.get("path"),
            "url": base + sub.get("path", "")
        })
    
    result.append(node)


# ===============================================
# crawler test
# ===============================================

with open("categories.json", "r", encoding="utf-8") as f:
    categories = json.load(f)

for cat in categories:
    cat_name = cat.get("name")
    subcats = cat.get("subcategories", [])

    for sub in subcats:
        sub_id = sub.get("id")
        sub_name = sub.get("name")
        
        offset = 0
        while True:
            url = f"https://arfigyelo.gvh.hu/api/products-by-category/{sub_id}?limit=24&offset={offset}&order=unitAmount_asc"
            
            r = requests.get(url, timeout=20)
            if r.status_code != 200:
                break
                
            data = r.json()
            products = data.get("products", [])
            total_count = data.get("count", 0)

            if not products:
                break

            for p in products:
                out = {
                    "product_id": p.get("id"),
                    "name": p.get("name"),
                    "category_path": p.get("categoryPath"),
                    "category": cat_name,
                    "subcategory": sub_name,
                    "image": p.get("imageUrl"),
                    "unit": p.get("unit"),
                    "packaging": p.get("packaging"),
                    "min_price": p.get("minUnitPrice"),
                    "chain_store_prices": [],
                }

                for store in p.get("pricesOfChainStores", []):
                    store_name = store.get("name")
                    for price_info in store.get("prices", []):
                        out["chain_store_prices"].append({
                            "store": store_name,
                            "amount": price_info.get("amount"),
                            "unit_amount": price_info.get("unitAmount"),
                            "type": price_info.get("type"),
                            "same_everywhere": price_info.get("sameAmountEverywhere"),
                        })

            offset += 24
            if offset >= total_count:
                break

            time.sleep(0.3)

"""
FINDINGS:
1. Category and subcategory URLs are obtained through the API, not available in HTML.

2. The crawler retrieves product details via API by parsing the category ID.

3. Product URLs are generated using the category path and product ID.

4. Parser does not need, all visible data extracts through crawler.
"""