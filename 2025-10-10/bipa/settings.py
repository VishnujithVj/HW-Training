from datetime import datetime
import os
import calendar
import logging
import configparser
import pytz
import requests
from dateutil.relativedelta import relativedelta, MO
from mongoengine import connect


# LOGGING CONFIGURATION
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/bipa_crawler.log"),
        logging.StreamHandler(),
    ],
)

# BASIC PROJECT DETAILS
PROJECT = "bipa"
CLIENT_NAME = "bipa"
PROJECT_NAME = "bipa"
FREQUENCY = ""
BASE_URL = "https://www.bipa.at"


# DATE AND TIME VARIABLES
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

# FILENAME  
FILE_NAME = f"{PROJECT_NAME}_{iteration}"

# DATABASE CONFIGURATION
MONGO_DB = f"{PROJECT_NAME}_db"

# COLLECTION NAMES
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category_urls"
MONGO_COLLECTION_URL = f"{PROJECT_NAME}_product_urls"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"
MONGO_COLLECTION_RESPONSE = f"{PROJECT_NAME}_response"
MONGO_COLLECTION_MISMATCH = f"{PROJECT_NAME}_mismatch"
MONGO_COLLECTION_EMPTY = f"{PROJECT_NAME}_empty"
MONGO_COLLECTION_COUNT = f"{PROJECT_NAME}_count"
MONGO_COLLECTION_PAGINATION = f"{PROJECT_NAME}_pagination"

# MongoDB Connection
connect(db=MONGO_DB, host=f"mongodb://localhost:27017/{MONGO_DB}", alias="default")

# SHARD COLLECTION CONFIG
MONGO_COL_URL = MONGO_COLLECTION_URL
SHARD_COLLECTION = [
    {"col": MONGO_COL_URL, "unique": True, "indexfield": "url"},
]

# HEADERS AND NETWORK CONFIG
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
}

COOKIES = {
            'OptanonAlertBoxClosed': '2025-10-20T10:04:09.055Z',
            'usid_AT': '22ba7b8d-30d6-44d2-9d3e-6cae00a296bb',
        }


# PAGINATION CONFIGURATION
PRODUCTS_PER_PAGE = 24


# EXPORT CONFIG
file_name = f"exports/{FILE_NAME}.csv"
os.makedirs("exports", exist_ok=True)

FILE_HEADERS = [
    "pdp_url",
    "unique_id",
    "product_name",
    "brand",
    "brand_type",
    "selling_price",
    "regular_price",
    "price_was",
    "promotion_price",
    "promotion_type",
    "percentage_discount",
    "promotion_description",
    "currency",
    "product_description",
    "producthierarchy_level1",
    "producthierarchy_level2",
    "producthierarchy_level3",
    "producthierarchy_level4",
    "producthierarchy_level5",
    "producthierarchy_level6",
    "producthierarchy_level7",
    "image_url_1",
    "image_url_2",
    "image_url_3",
    "breadcrumb",
    "instock",
    "extraction_date"
]