from datetime import datetime
import os
import calendar
import logging
import configparser
import pytz
from dateutil.relativedelta import relativedelta, MO

"""LOGGING"""
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

"""PROJECT DETAILS"""
PROJECT = "luluhypermarket"
CLIENT_NAME = "luluhypermarket"
PROJECT_NAME = "lulu"
FREQUENCY = ""

BASE_URL = "https://gcc.luluhypermarket.com/"

"""DATE / ITERATION SETTINGS"""
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip('0'))]
WEEK = (int(DAY) - 1) // 7 + 1    

FILE_NAME = f"{PROJECT_NAME}_{iteration}.csv"

"""MONGO SETTINGS"""
MONGO_HOST = "mongodb://localhost:27017/"
MONGO_DB = f"{PROJECT}_db"

MONGO_COLLECTION_URL = f"{PROJECT_NAME}_url"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"
MONGO_COLLECTION_RESPONSE = f"{PROJECT_NAME}_responses"

"""SHARD / INDEX CONFIG"""
SHARD_COLLECTION = [
    {"col": MONGO_COLLECTION_URL, "unique": True, "indexfield": "url"},
]

"""HEADERS"""
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
}

File_Headers = [
            "product_id", "url", "product_name", "product_color", "material",
            "quantity", "details_string", "specification", "product_type",
            "price", "wasPrice", "breadcrumb", "stock", "image"
        ]