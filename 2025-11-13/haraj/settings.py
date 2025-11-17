from datetime import datetime
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

"""Project details"""
PROJECT = "haraj"
CLIENT_NAME = "haraj"
PROJECT_NAME = "haraj_property"
FREQUENCY = ""
BASE_URL = "https://haraj.com.sa/"

datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT_NAME}_{iteration}.csv"

"""MONGO SETTINGS""" 
MONGO_DB = f"{PROJECT_NAME}_db"
MONGO_HOST = "mongodb://localhost:27017/"

"""Collection names"""
MONGO_COLLECTION_URL = f"{PROJECT_NAME}_url"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"
MONGO_COLLECTION_PAGINATION = f"{PROJECT_NAME}_pagination"
MONGO_COLLECTION_POST_URL = f"{PROJECT_NAME}_post_url"
MONGO_COLLECTION_POST_ITEM = f"{PROJECT_NAME}_item"

"""Headers"""
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version-list': '"Google Chrome";v="141.0.7390.54", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.54"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Linux"',
    'sec-ch-ua-platform-version': '""',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
}

API_URL = "https://api.dealapp.sa/production/ad/{ad_id}"

FILE_HEADERS = ["Reference Number", "Property ID", "URL", "Title", "Description",
                "Location", "Price", "Currency", "Price Per", "Bedrooms",
                "Bathrooms", "Furnished", "RERA Permit Number", "DTCM Licence",
                "Amenities", "Number of Photos", "Phone Number"]


