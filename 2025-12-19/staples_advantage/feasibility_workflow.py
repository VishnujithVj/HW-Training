
import requests
import json
from parsel import Selector

# =================================
# catgeory_test.py
# =================================

url = "https://www.staplesadvantage.com"
res = requests.get(url)

sel = Selector(res.text)

# Extract script text
script_text = sel.xpath("//script[@id='__NEXT_DATA__']/text()").get()
# Convert to JSON
data = json.loads(script_text)

json_data = data.get("props", {}).get("initialStateOrStore", {}).get("headerState", {}).get("sparq-index", {}).get("seoL1Links", [])
for key in json_data:
    ariels = key.get("ariaLabel")
    url = key.get("destinationURL")
    # print(ariels, url)  main category links

# =================================
# sub catgeory_test.py
# =================================

BASE_URL = "https://www.staplesadvantage.com"
START_URL = "https://www.staplesadvantage.com/office-supplies/cat_SC273214" # single - main catgeory

response = requests.get(START_URL)
sel = Selector(response.text)

category_tree = []

# Level 1: subcategories
subcategories = sel.xpath("//a[@class='seo-component__seoLink']/@href").getall()

for subcat in subcategories:
    subcat_url = f"{BASE_URL}{subcat}"
    res2 = requests.get(subcat_url)
    sel2 = Selector(res2.text)

    subcat_node = {
        "category_url": subcat_url,
        "children": []
    }

    # Level 2: sub-subcategories (same XPath)
    sub_subcategories = sel2.xpath("//a[@class='seo-component__seoLink']/@href").getall()

    if sub_subcategories:
        for ssub in sub_subcategories:
            ssub_url = f"{BASE_URL}{ssub}"

            subcat_node["children"].append({
                "subcategory_url": ssub_url
            })
    else:
        subcat_node["children"] = []

    category_tree.append(subcat_node)

# ============================================
# crawler_test.py
# ============================================

# Extract script text
script_text = sel.xpath("//script[@id='__NEXT_DATA__']/text()").get()

# Convert to JSON
data = json.loads(script_text)

products=data.get("props",{}).get("initialStateOrStore",{}).get("searchState",{}).get("itemData",[])
for product in products:
    sku=product.get("compareItemID")
    site_url=product.get("url")
    product_title=product.get("title")
    brand=product.get("brandName")
    rating=product.get("rating")
    category=product.get("baseCatName")
    cost=product.get("price")
    notes=product.get("description")


# ==================================================
# findings
# ==================================================

"""
1. The main category links can be extracted from the headerState -> sparq-index -> seoL1Links section of the __NEXT_DATA__ script tag.
2. 2.Products are available within the scripts of PLP pages with data  and no parser-based extraction is currently required.

"""