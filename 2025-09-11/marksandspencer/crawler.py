import requests
from parsel import Selector
from urllib.parse import urljoin
import time
import logging
from datetime import datetime
from pymongo import MongoClient

# CONFIG
BASE_URL = "https://www.marksandspencer.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}
REQUEST_DELAY = 1

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["marksandspencer"]
categories_col = db["categories"]

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)

def get_categories():
    """Get main category links from homepage"""
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        sel = Selector(response.text)

        category_links = sel.xpath(
            '//a[contains(@class,"analytics-department-carousel_cardWrapper")]/@href'
        ).getall()
        category_links = [urljoin(BASE_URL, link) for link in category_links]

        return list(set(category_links))
    except Exception as e:
        logging.error(f"Error fetching categories: {e}")
        return []


def get_subcategories(category_url):
    """Get subcategory links from a category page"""
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(category_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        sel = Selector(response.text)

        sub_links = sel.xpath(
            '//nav[contains(@class,"circular-navigation_circularNavigationBox")]//a/@href'
        ).getall()
        sub_links = [urljoin(BASE_URL, s) for s in sub_links]

        return list(set(sub_links))
    except Exception as e:
        logging.error(f"Error getting subcategories from {category_url}: {e}")
        return []


def get_product_links(subcategory_url, max_products=None):
    """Get product links from ALL pages of a subcategory"""
    product_links = []
    page_url = subcategory_url

    try:
        while page_url:
            time.sleep(REQUEST_DELAY)
            response = requests.get(page_url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            sel = Selector(response.text)

            # Extract product links
            new_links = sel.xpath('//a[contains(@href, "/p/")]/@href').getall()
            new_links = [urljoin(BASE_URL, link) for link in new_links if "/p/" in link]

            product_links.extend(new_links)
            product_links = list(set(product_links))  

            
            if max_products and len(product_links) >= max_products:
                return product_links[:max_products]

            next_page = sel.xpath(
                '//a[contains(@class,"pagination-button--next") or contains(@data-test,"pagination-next")]/@href'
            ).get()

            if next_page:
                page_url = urljoin(BASE_URL, next_page)
                logging.info(f"    Moving to next page: {page_url}")
            else:
                page_url = None  

        return product_links

    except Exception as e:
        logging.error(f"Error getting products from {subcategory_url}: {e}")
        return []


# MAIN
if __name__ == "__main__":
    logging.info("Starting crawler...")

    categories = get_categories()
    logging.info(f"Found {len(categories)} main categories")

    catalog_data = []
    all_products = []

    for category in categories:
        logging.info(f"Getting subcategories for: {category}")
        subcategories = get_subcategories(category)

        category_data = {
            "category_url": category,
            "subcategories": [],
            "timestamp": datetime.utcnow()
        }

        for subcategory in subcategories:
            logging.info(f"  Getting products from: {subcategory}")
            products = get_product_links(subcategory, max_products=50)  # None = no limit

            subcategory_data = {
                "subcategory_url": subcategory,
                "products": products,
                "product_count": len(products),
                "timestamp": datetime.utcnow()
            }

            category_data["subcategories"].append(subcategory_data)
            all_products.extend(products)

        try:
            categories_col.insert_one(category_data)
            logging.info(f"Inserted category data for {category}")
        except Exception as db_err:
            logging.error(f"Error inserting into MongoDB: {db_err}")

        catalog_data.append(category_data)

    logging.info(
        f"Crawling complete! Categories: {len(catalog_data)}, "
        f"Subcategories: {sum(len(cat['subcategories']) for cat in catalog_data)}, "
        f"Products: {len(all_products)}"
    )
