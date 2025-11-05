""" FEASIBILITY WORKFLOW REPORT - FATFACE.COM """

import requests
from parsel import Selector
from pymongo import MongoClient
import math
import re
from urllib.parse import urljoin


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Priority': 'u=0, i',
}

""" CATEGORY CRAWLER """
API_URL = "https://www.fatface.com/headerstatic/seo-content"
BASE_URL = "https://www.fatface.com"

""" Fetch category JSON data from API """
response = requests.get(API_URL, headers=headers, timeout=30)
category_data = response.json().get("items", [])

""" Extract categories recursively """
def parse_categories(data):
    results = []

    def recurse(items, parent_title= "", parent_url= ""):
        for item in items:
            title = item.get("title")
            target = item.get("target")
            if not title or not target:
                continue

            url = urljoin(BASE_URL, target.strip())

            results.append({
                "category_title": parent_title or title,
                "subcategory_title": title if parent_title else "",
                "category_url": parent_url or url,
                "subcategory_url": url if parent_title else "",

            })

            """ recurse if has nested items """
            if isinstance(item.get("items"), list):
                recurse(item["items"], parent_title=title, parent_url=url)

    recurse(data)
    return [r for r in results if r["subcategory_url"]]

subcategories = parse_categories(category_data)
print(f"Found {len(subcategories)} subcategories")


""" PRODUCT CRAWLER """
subcategory_url = subcategories[0]["subcategory_url"] if subcategories else ""
category_url = subcategories[0]["category_url"] if subcategories else ""

""" Paginate through product listings """
page = 1
total_pages = None
total_products = 0
seen = set()
product_urls = []

while True:
    page_url = f"{subcategory_url.split('?')[0]}?p={page}"
    print(f"Fetching page {page}: {page_url}")

    response = requests.get(page_url, headers=headers, timeout=30)
    sel = Selector(text=response.text)

    """ Extract total product count on first page """
    if page == 1:
        count_text = sel.xpath('//span[@class="esi-count"]/text()').get()
        if count_text:
            total_products = int(''.join([c for c in count_text if c.isdigit()]) or 0)
            print(f"Total products listed: {total_products}")

    """ Extract product URLs """
    product_links = sel.xpath('//a[contains(@class,"MuiCardMedia-root")]/@href').getall()
    product_links = [urljoin(BASE_URL, href.split('#')[0]) for href in product_links if href.strip()]

    if not product_links:
        print("No more product links found. Ending pagination.")
        break

    new_links = [link for link in product_links if link not in seen]
    seen.update(new_links)
    product_urls.extend(new_links)

    print(f"Page {page}: {len(new_links)} new products found")

    """ Pagination logic """
    if total_products and not total_pages:
        per_page = len(product_links)
        total_pages = math.ceil(total_products / per_page) if per_page else 1
        print(f"Total estimated pages: {total_pages}")

    if total_pages and page >= total_pages:
        break

    page += 1

print(f"Total product URLs collected: {len(product_urls)}")


""" PARSER """
# Test with first product URL
if product_urls:
    test_product_url = product_urls[0]
    print(f"Testing parser with: {test_product_url}")
    
    response = requests.get(test_product_url, headers=headers, timeout=30)
    sel = Selector(text=response.text)

    # Product Code
    UNIQUE_ID = '//h2[contains(text(),"Product Code")]/following-sibling::span/text()'
    unique_id = sel.xpath(UNIQUE_ID).get()
    unique_id = re.sub(r"\s+", " ", unique_id).strip() if unique_id else ""

    # Product Name 
    PRODUCT_NAME = '//h1[@data-testid="product-title"]/text()'
    product_name = sel.xpath(PRODUCT_NAME).get()
    product_name = re.sub(r"\s+", " ", product_name).strip() if product_name else ""

    # Price
    PRICE = '//div[@data-testid="product-now-price"]/span/text()'
    price = sel.xpath(PRICE).get()
    price = price.strip() if price else "",

    # Product Description 
    DESCRIPTION = '//div[@data-testid="item-description"]//text()'
    description = " ".join(sel.xpath(DESCRIPTION).getall())
    description = re.sub(r"\s+", " ", description).strip() if description else ""

    # Images 
    IMAGES = '//div[@data-testid="image-gallery-slide"]//img/@src'
    images = sel.xpath(IMAGES).getall()
    images = [urljoin(BASE_URL, i) for i in images if i.strip()]


############################## FINDINGS ##############################

# - Category structure available via API endpoint (/headerstatic/seo-content)
# - Pagination uses simple ?p= parameter like this (?p=1, ?p=2, ...).
# - Product URLs extracted from MuiCardMedia-root class anchors
# - Product details well-structured with data-testid attributes
# - Product code available as unique identifier
# - Images available in gallery with multiple views
# - Rating and review count available on PDP
# - Available Product details (title, price, colour, image ,review, rating, description, product_id, fit, care & fabric) are accessible in  HTML.
# - Crawling can proceed safely using polite delays.

