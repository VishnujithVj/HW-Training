import logging
from mongoengine import connect
from datetime import datetime
import pytz
import os

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bipa_crawler.log"),
        logging.StreamHandler()
    ]
)

PROJECT_NAME = "bipa"
BASE_URL = "https://www.bipa.at"

datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")

# Mongo db and collections
MONGO_DB = "bipa_db3"
MONGO_COLLECTION_CATEGORY = "category_urls"
MONGO_COLLECTION_URL = "product_urls"
MONGO_COLLECTION_DATA = "product_data"

# MongoDB connection
connect(db=MONGO_DB, host="mongodb://localhost:27017/" + MONGO_DB, alias="default")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# Pagination settings
PRODUCTS_PER_PAGE = 24