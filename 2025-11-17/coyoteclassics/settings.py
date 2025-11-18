import logging
from datetime import datetime
import pytz
import calendar

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------- Project details ----------
PROJECT = "coyoteclassics"
CLIENT_NAME = ""
PROJECT_NAME = "coyoteclassics"
BASE_URL = "https://www.coyoteclassics.com"

# ---------- Time / filenames ----------
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT}_{iteration}"
CSV_FILE = f"{FILE_NAME}.csv"

# ---------- Mongo ----------
MONGO_HOST = "mongodb://localhost:27017/"
MONGO_DB = f"{PROJECT}_db"

MONGO_COLLECTION_URL = f"{PROJECT}_urls"
MONGO_COLLECTION_DATA = f"{PROJECT}_data"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT}_url_failed"

# ---------- Request headers ----------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

# ---------- Exporter ----------
FILE_HEADERS = [
    "source_link",
    "year",
    "make",
    "model",
    "vin",
    "price",
    "mileage",
    "transmission",
    "engine",
    "color",
    "fuel_type",
    "body_style",
    "description",
    "image_urls",
]
