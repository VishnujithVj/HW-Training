# import requests
# from lxml import html
# import os
# import re
# import json

# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
#                   "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
# }

# def parse_pdp(pdp_url):
#     os.makedirs("data/raw_html", exist_ok=True)

#     response = requests.get(pdp_url, headers=HEADERS, timeout=20)
#     fname = pdp_url.strip("/").replace("https://", "").replace("/", "_")
#     with open(f"data/raw_html/{fname}_pdp.html", "wb") as f:
#         f.write(response.content)

#     tree = html.fromstring(response.content)

#     product_data = {
#         "unique_id": "".join(re.findall(r"\d+", pdp_url)),
#         "product_name": tree.xpath('normalize-space(//h1)'),
#         "brand": "Marks & Spencer",
#         "category": tree.xpath('normalize-space(//nav[contains(@class,"breadcrumb")]//li[last()]/a/text())'),
#         "regular_price": tree.xpath('normalize-space((//span[contains(@class,"price") and contains(text(),"£")])[1])'),
#         "selling_price": tree.xpath('normalize-space((//span[contains(@class,"price") and contains(text(),"£")])[last()])'),
#         "promotion_description": tree.xpath('normalize-space(//span[contains(@class,"promo") or contains(@class,"promotion")]/text())'),
#         "breadcrumb": tree.xpath('//nav[contains(@class,"breadcrumb")]//a/text()'),
#         "pdp_url": pdp_url,
#         "product_description": " ".join(tree.xpath('//div[contains(@class,"product-description")]//text()')).strip(),
#         "currency": "GBP",
#         "color": tree.xpath('//ul[contains(@class,"colour-swatch")]//span/text()'),
#         "size": tree.xpath('//ul[contains(@class,"size-list")]//span/text()'),
#         "rating": tree.xpath('normalize-space(//span[contains(@class,"rating")]/text())'),
#         "review": tree.xpath('//span[contains(@class,"review-count")]/text()'),
#         "material_composition": tree.xpath('normalize-space(//li[contains(text(),"Composition")]/text())'),
#         "style": tree.xpath('normalize-space(//li[contains(text(),"Style")]/text())'),
#         "care_instructions": tree.xpath('normalize-space(//li[contains(text(),"Care")]/text())'),
#         "feature": tree.xpath('//ul[contains(@class,"features")]//li/text()'),
#         "images": tree.xpath('//img[contains(@class,"product-image")]/@src'),
#         "composition": tree.xpath('normalize-space(//div[contains(@class,"composition")]/text())')
#     }

#     return product_data


# if __name__ == "__main__":
#     # Load PDP links collected by crawler
#     with open("data/pdp_links.json", "r", encoding="utf-8") as f:
#         pdp_links = json.load(f)

#     all_products = []
#     for i, pdp_url in enumerate(pdp_links, 1):
#         try:
#             print(f"[{i}/{len(pdp_links)}] Parsing PDP: {pdp_url}")
#             data = parse_pdp(pdp_url)
#             all_products.append(data)
#         except Exception as e:
#             print("❌ Error parsing PDP:", pdp_url, e)

#     # Save results JSON
#     os.makedirs("data", exist_ok=True)
#     with open("data/pdp_data.json", "w", encoding="utf-8") as f:
#         json.dump(all_products, f, indent=2, ensure_ascii=False)

#     # Save results CSV
#     if all_products:
#         import csv
#         keys = all_products[0].keys()
#         with open("data/pdp_data.csv", "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=keys)
#             writer.writeheader()
#             writer.writerows(all_products)

#     print(f"✅ Parsed {len(all_products)} products. Data saved to data/pdp_data.json and data/pdp_data.csv")
# --------------------------------------------------------------------------------------------------------------------------------------------

import requests
from lxml import html
import json
import csv
import re
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def parse_product(product_url):
    """Parse product data from a product page"""
    try:
        response = requests.get(product_url, headers=HEADERS, timeout=20)
        tree = html.fromstring(response.content)
        
        # Helper function to safely extract data
        def safe_xpath(query,n=0, default="Not found"):
            result = tree.xpath(query)
            return result[n].strip() if result else default
    
        
        def safe_xpath_list(query, default=[]):
            result = tree.xpath(query)
            return [item.strip() for item in result] if result else default
        
        # Extract product data
        product_data = {
            "unique_id": safe_xpath('//p[@class="media-0_textXs__ZzHWu"]/text()',1),
            "product_name": safe_xpath('//h1/text()'),
            "brand": "Marks & Spencer",
            "category": safe_xpath('(//li[@class="breadcrumb_listItem__oW_Gf"]/a)[last()]/text()'),
            "breadcrumb": ", ".join(safe_xpath_list('//li[@class="breadcrumb_listItem__oW_Gf"]/a/text()')),
            "price": safe_xpath('//p[(@class="media-0_headingSm__aysOm")]/text()').replace("£", "").strip(),
            "product_url": product_url,
            "description": safe_xpath('//p[(@class="media-0_textSm__Q52Mz")]//text()',1),
            "color": safe_xpath('//span[@class="media-0_textSm__Q52Mz"]/text()',3),
            "size": ", ".join(safe_xpath_list('//span[@class="media-0_body__yf6Z_"]/text()')),
            "rating": safe_xpath('//span[@class="media-0_textXs__ZzHWu media-768_textSm__oojIW rating_score__LUhRP"]/text()'),
        }
        
        return product_data
    except Exception as e:
        print(f"Error parsing {product_url}: {e}")
        return None

def append_to_master_files(product_data, csv_writer):
    """Append product data to master files"""
    # Append to master JSON file
    master_json = "data/all_products.json"
    if os.path.exists(master_json):
        with open(master_json, "r") as f:
            all_data = json.load(f)
    else:
        all_data = []
    
    all_data.append(product_data)
    with open(master_json, "w") as f:
        json.dump(all_data, f, indent=2)
    
    # Append to master CSV
    csv_writer.writerow(list(product_data.values()))

if __name__ == "__main__":
    print("Starting parser...")
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Load product links
    with open("products.json", "r") as f:
        product_urls = json.load(f)
    
    # Prepare master CSV file
    master_csv = "data/all_products.csv"
    with open(master_csv, "w", newline="", encoding="utf-8") as f:
        # Get fieldnames from first product (if available) or use default
        fieldnames = [
            "unique_id", "product_name", "brand", "category", "price", 
            "product_url", "description", "color", "size", "rating"
        ]
        csv_writer = csv.writer(f)
        csv_writer.writerow(fieldnames)
        
        # Parse and save each product one at a time
        for i, url in enumerate(product_urls[:10], 1):
            print(f"Parsing product {i}/10: {url}")
            product_data = parse_product(url)

            if product_data:

                # Append to master files
                append_to_master_files(product_data, csv_writer)
            else:
                print(f"  Failed to parse product {i}")
    
    print(f"\nParsing complete! Processed {len(product_urls[:10])} products")