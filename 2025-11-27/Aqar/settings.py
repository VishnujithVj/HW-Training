from datetime import datetime
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Project Details
PROJECT = "aqar"
CLIENT_NAME = "Peter"
PROJECT_NAME = "aqar"
FREQUENCY = "POC"
BASE_URL = "https://sa.aqar.fm/"

# Time-based values
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")

YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT_NAME}_sa_{iteration}_sample.csv"

# MongoDB
MONGO_DB = f"{PROJECT_NAME}_db"
MONGO_COLLECTION_URL = f"{PROJECT_NAME}_urls"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category_url"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"
MONGO_COLLECTION_PAGINATION = f"{PROJECT_NAME}_pagination_url"



# Headers
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}

FILE_HEADERS = [
"id",
"reference_number",
"url",
"broker_display_name",
"broker",
"category",
"category_url",
"title",
"description",
"location",
"price",
"currency",
"price_per",
"bedrooms",
"bathrooms",
"furnished",
"rera_permit_number",
"dtcm_licence",
"scraped_ts",
"amenities",
"details",
"agent_name",
"number_of_photos",
"user_id",
"phone_number",
"date",
"iteration_number",
"depth",
"property_type",
"sub_category_1",
"sub_category_2",
"published_at"
]