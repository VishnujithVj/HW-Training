from datetime import datetime
import os
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Basic details
PROJECT = "elcorteingles"
CLIENT_NAME = "elcorteingles"
PROJECT_NAME = "elcorteingles"
FREQUENCY = "weekly"
BASE_URL = "https://www.elcorteingles.es/"

datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"elcorteingles_{iteration}"

# MongoDB and collections
MONGO_DB = f"elcorteingles_db"
MONGO_COLLECTION_INPUT = f"input_details"
MONGO_COLLECTION_MATCHED = f"matched_products"
MONGO_COLLECTION_DATA = f"product_data2"

# MongoDB connection
MONGO_URI = ("mongodb://localhost:27017")



# Headers and useragents
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/142.0.0.0 Safari/537.36",
}

# Search configuration
SEARCH_BASE_URL = "https://www.elcorteingles.es/search-nwx/1/"
FUZZY_MATCH_THRESHOLD = 70
EXACT_MATCH_SCORE = 100

# Rate limiting
REQUEST_DELAY = 1  # seconds between requests
REQUEST_TIMEOUT = 20  # seconds