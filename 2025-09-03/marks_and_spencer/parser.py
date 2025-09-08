 
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
        
        def safe_xpath(query,n=0, default="Not found"):
            result = tree.xpath(query)
            return result[n].strip() if result else default
    
        
        def safe_xpath_list(query, default=[]):
            result = tree.xpath(query)
            return [item.strip() for item in result] if result else default
        
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
    master_json = "data/all_products.json"
    if os.path.exists(master_json):
        with open(master_json, "r") as f:
            all_data = json.load(f)
    else:
        all_data = []
    
    all_data.append(product_data)
    with open(master_json, "w") as f:
        json.dump(all_data, f, indent=2)
    
    csv_writer.writerow(list(product_data.values()))

if __name__ == "__main__":
    print("Starting parser...")
    
    os.makedirs("data", exist_ok=True)
    
    with open("products.json", "r") as f:
        product_urls = json.load(f)
    
    master_csv = "data/all_products.csv"
    with open(master_csv, "w", newline="", encoding="utf-8") as f:
    
        fieldnames = [
            "unique_id", "product_name", "brand", "category", "price", 
            "product_url", "description", "color", "size", "rating"
        ]
        csv_writer = csv.writer(f)
        csv_writer.writerow(fieldnames)
        
        for i, url in enumerate(product_urls[:10], 1):
            print(f"Parsing product {i}/10: {url}")
            product_data = parse_product(url)

            if product_data:

            
                append_to_master_files(product_data, csv_writer)
            else:
                print(f"  Failed to parse product {i}")
    
    print(f"\nParsing complete! Processed {len(product_urls[:10])} products")