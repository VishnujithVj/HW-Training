from datetime import datetime
import os
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s", datefmt="%Y-%m-%d %H:%M:%S",)

PROJECT = "officedepot"
CLIENT_NAME = "officedepot"
PROJECT_NAME = "officedepot"
FREQUENCY = "onetime"
BASE_URL = "https://www.officedepot.com/"

datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"officedepot_{iteration}"

"""Mongo db and collections"""
MONGO_DB = f"officedepot_db2"
MONGO_COLLECTION_PRODUCT_URL = f"{PROJECT_NAME}_product_url2"
MONGO_COLLECTION_RESPONSE = f"{PROJECT_NAME}_response"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category_url"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"



"""Headers and useragents"""
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

SHARD_COLLECTION = [
    {'col': MONGO_COLLECTION_PRODUCT_URL, 'unique': True, 'indexfield': "url"},
]

FILE_HEADERS = [
    "Company Name",
    "Manufacturer Name",
    "Brand Name",
    "Vendor/Seller Part Number",
    "Item Name",
    "Full Product Description",
    "Price",
    "Unit of Issue",
    "QTY Per UOI",
    "Product Category",
    "URL",
    "Availability",
    "Manufacturer Part Number",
    "Country of Origin",
    "UPC",
    "Model Number",
]