from datetime import datetime
import calendar
import logging
import configparser
import pytz
from dateutil.relativedelta import relativedelta, MO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# basic details
PROJECT = "qatar_living_properties"
CLIENT_NAME = "qatar_living"
PROJECT_NAME = "qlp"
FREQUENCY = ""
BASE_URL = "https://qlpbackendprod.azurewebsites.net/"


datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"qatar_living_properties_{iteration}.csv"

# Mongo db and collections
MONGO_DB = f"qatar_living_properties_{iteration}"
MONGO_COL_URL = f"{PROJECT_NAME}_product_url"
MONGO_COLLECTION_RESPONSE = f"{PROJECT_NAME}_url"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category_url"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"


SHARD_COLLECTION = [
    {'col': MONGO_COL_URL, 'unique': True, 'indexfield': "url"}, ]


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': 'https://qlp.qatarliving.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}

# Qatar Living Properties specific settings
PROPERTIES_BASE_URL = "https://qlpbackendprod.azurewebsites.net/properties"
PER_PAGE = 20
CATEGORIES = [1, 2, 3, 4, 5]  # Categories 1 to 5