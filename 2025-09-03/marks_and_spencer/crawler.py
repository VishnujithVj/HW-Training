import requests
from lxml import html
from urllib.parse import urljoin
import json
import time

BASE_URL = "https://www.marksandspencer.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

REQUEST_DELAY = 1

def get_categories():
    """Get main category links from homepage"""
    response = requests.get(BASE_URL, headers=HEADERS, timeout=20)
    tree = html.fromstring(response.content)
    
    category_links = tree.xpath('//a[contains(@class,"analytics-department-carousel_cardWrapper")]/@href')
    category_links = [urljoin(BASE_URL, link) for link in category_links]
    
    return list(set(category_links))

def get_subcategories(category_url):
    """Get subcategory links from a category page"""
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(category_url, headers=HEADERS, timeout=20)
        tree = html.fromstring(response.content)
        
        sub_links = tree.xpath('//nav[contains(@class,"circular-navigation_circularNavigationBox")]//a/@href')
        sub_links = [urljoin(BASE_URL, s) for s in sub_links]
        
        return list(set(sub_links))
    except Exception as e:
        print(f"Error getting subcategories from {category_url}: {e}")
        return []

def get_product_links(subcategory_url, max_products=10):
    """Get product links from a subcategory page (first page only) - max 10 products"""
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(subcategory_url, headers=HEADERS, timeout=20)
        tree = html.fromstring(response.content)
        
        selectors = [
            '//a[contains(@href, "/p/")]/@href',
            '//a[contains(@class, "product-card")]/@href',
            '//a[contains(@data-test, "product-card")]/@href'
        ]
        
        product_links = []
        for selector in selectors:
            links = tree.xpath(selector)
            if links:
                product_links.extend(links)
        
        product_links = [urljoin(BASE_URL, link) for link in product_links if "/p/" in link]
        product_links = list(set(product_links))
        
        return product_links[:max_products]
    except Exception as e:
        print(f"Error getting products from {subcategory_url}: {e}")
        return []

if __name__ == "__main__":
    print("Starting crawler...")
    
    categories = get_categories()
    print(f"Found {len(categories)} main categories")
    
    catalog_data = []
    all_products = []
    
    for category in categories:
        print(f"\nGetting subcategories for: {category}")
        subcategories = get_subcategories(category)
        
        category_data = {
            "category_url": category,
            "subcategories": []
        }
    
        for subcategory in subcategories:
            print(f"  Getting products from: {subcategory}")
            products = get_product_links(subcategory, max_products=10) 
            
            subcategory_data = {
                "subcategory_url": subcategory,
                "products": products,
                "product_count": len(products)
            }
            
            category_data["subcategories"].append(subcategory_data)
            all_products.extend(products)
            
        catalog_data.append(category_data)
    
    with open("catalog_structure.json", "w") as f:
        json.dump(catalog_data, f, indent=2)
    
    with open("products.json", "w") as f:
        json.dump(all_products, f, indent=2)
    
    total_subcategories = sum(len(cat["subcategories"]) for cat in catalog_data)
    total_products = len(all_products)
    
    print(f"\nCrawling complete!")
    print(f"Categories processed: {len(catalog_data)}")
    print(f"Subcategories processed: {total_subcategories}")
    print(f"Total products collected: {total_products}")
    print("Files saved: catalog_structure.json, products.json")