# import requests
# from lxml import html
# from urllib.parse import urljoin
# import os
# import json

# BASE_URL = "https://www.marksandspencer.com/"
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
#                   "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
# }

# def crawl_categories_and_subcategories():
#     os.makedirs("data/raw_html", exist_ok=True)

#     # Homepage
#     response = requests.get(BASE_URL, headers=HEADERS, timeout=20)
#     with open("data/raw_html/homepage.html", "wb") as f:
#         f.write(response.content)
#     print("Homepage status:", response.status_code)

#     tree = html.fromstring(response.content)

#     # Top categories
#     category_links = tree.xpath('//a[contains(@class,"analytics-department-carousel_cardWrapper")]/@href')
#     category_links = [urljoin(BASE_URL, link) for link in category_links]
#     category_links = list(set(category_links))

#     all_subcategories = []
#     for cat_url in category_links:
#         print(f"\nFetching category: {cat_url}")
#         try:
#             resp = requests.get(cat_url, headers=HEADERS, timeout=20)
#             sub_tree = html.fromstring(resp.content)

#             # Subcategory links inside circular navigation
#             sub_links = sub_tree.xpath('//nav[contains(@class,"circular-navigation_circularNavigationBox")]//a/@href')
#             sub_links = [urljoin(BASE_URL, s) for s in sub_links]
#             sub_links = list(set(sub_links))

#             print(f"  Found {len(sub_links)} sub-categories")
#             all_subcategories.extend(sub_links)

#         except Exception as e:
#             print("  Error fetching:", e)

#     return list(set(all_subcategories))  # return unique subcategories


# def crawl_plp_first_page(category_url):
#     response = requests.get(category_url, headers=HEADERS, timeout=20)
#     fname = category_url.strip("/").replace("https://", "").replace("/", "_")
#     with open(f"data/raw_html/{fname}_plp.html", "wb") as f:
#         f.write(response.content)

#     tree = html.fromstring(response.content)

#     # PDP links (first page only)
#     pdp_links = tree.xpath('//a[contains(@class,"product-card_link")]/@href')
#     pdp_links = [urljoin(BASE_URL, link) for link in pdp_links]

#     return pdp_links


# if __name__ == "__main__":
#     subcategories = crawl_categories_and_subcategories()
#     print(f"\nTotal subcategories collected: {len(subcategories)}")

#     all_pdp_links = []
#     for sub_url in subcategories:
#         print(f"Fetching first page PDPs from: {sub_url}")
#         try:
#             links = crawl_plp_first_page(sub_url)
#             all_pdp_links.extend(links)
#         except Exception as e:
#             print("❌ Error fetching PLP:", sub_url, e)

#     # Save PDP links
#     os.makedirs("data", exist_ok=True)
#     with open("data/pdp_links.json", "w", encoding="utf-8") as f:
#         json.dump(all_pdp_links, f, indent=2)

#     print(f"✅ Collected {len(all_pdp_links)} PDP links")
# -----------------------------------------------------------------------------------------------------------------------

import requests
from lxml import html
from urllib.parse import urljoin
import json
import time

BASE_URL = "https://www.marksandspencer.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}
# Add a delay between requests to be respectful to the server
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
        
        # Try multiple selectors to find product links
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
        
        # Convert to absolute URLs and filter for product pages
        product_links = [urljoin(BASE_URL, link) for link in product_links if "/p/" in link]
        product_links = list(set(product_links))
        
        # Return only up to max_products
        return product_links[:max_products]
    except Exception as e:
        print(f"Error getting products from {subcategory_url}: {e}")
        return []

if __name__ == "__main__":
    print("Starting crawler...")
    
    # Get all categories
    categories = get_categories()
    print(f"Found {len(categories)} main categories")
    
    # Structure to store category -> subcategories -> products
    catalog_data = []
    all_products = []
    
    # Process each category
    for category in categories:
        print(f"\nGetting subcategories for: {category}")
        subcategories = get_subcategories(category)
        
        category_data = {
            "category_url": category,
            "subcategories": []
        }
        
        # Process each subcategory
        for subcategory in subcategories:
            print(f"  Getting products from: {subcategory}")
            products = get_product_links(subcategory, max_products=10)  # Get up to 10 products per subcategory
            
            subcategory_data = {
                "subcategory_url": subcategory,
                "products": products,
                "product_count": len(products)
            }
            
            category_data["subcategories"].append(subcategory_data)
            all_products.extend(products)
            
        catalog_data.append(category_data)
    
    # Save category-subcategory structure as JSON
    with open("catalog_structure.json", "w") as f:
        json.dump(catalog_data, f, indent=2)
    
    # Save all product URLs
    with open("products.json", "w") as f:
        json.dump(all_products, f, indent=2)
    
    # Calculate statistics
    total_subcategories = sum(len(cat["subcategories"]) for cat in catalog_data)
    total_products = len(all_products)
    
    print(f"\nCrawling complete!")
    print(f"Categories processed: {len(catalog_data)}")
    print(f"Subcategories processed: {total_subcategories}")
    print(f"Total products collected: {total_products}")
    print("Files saved: catalog_structure.json, products.json")