from datetime import datetime
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ==========================
# BASIC DETAILS
# ==========================
PROJECT = "jabra"
CLIENT_NAME = "jabra"
PROJECT_NAME = "jabra"
FREQUENCY = "one_time"
BASE_URL = "https://www.jabra.com/"

# ==========================
# DATE INFORMATION
# ==========================
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"jabra_{iteration}"

# ==========================
# MONGO DB AND COLLECTIONS
# ==========================
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = f"jabra_db2"

MONGO_COLLECTION_PRODUCT_IDS = f"{PROJECT_NAME}_product_ids"
MONGO_COLLECTION_GROUP_IDS = f"{PROJECT_NAME}_group_ids"
MONGO_COLLECTION_PRODUCT_DETAILS = f"{PROJECT_NAME}_product_details"
MONGO_COLLECTION_PRODUCT_URLS = f"{PROJECT_NAME}_product_urls"
MONGO_COLLECTION_DOCUMENTS = f"{PROJECT_NAME}_documents"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_product_data"

# ==========================
# API ENDPOINTS
# ==========================
PRODUCT_SEARCH_URL = "https://sfcc-prod-api.jabra.com/s/jabra-amer/dw/shop/v24_1/product_search"
PRODUCTS_BATCH_URL = "https://sfcc-prod-api.jabra.com/s/jabra-amer/dw/shop/v24_1/products"
GROUP_ATTRIBUTES_URL = "https://productcatalogueapi.jabra.com/v1/group/attributes"
DOCUMENTS_URL = "https://knowledgebaseapi.jabra.com/v1/group/{group_id}/documents"

# ==========================
# API PARAMETERS
# ==========================
PRODUCT_SEARCH_PARAMS = {
    "refine_1": "c_countryProductState=3",
    "expand": "prices",
    "locale": "en-US",
    "refine_2": "orderable_only=true",
    "refine_3": "c_countryOnlineFlag=1",
    "refine_4": "c_portfolio=Jabra",
    "refine_5": "c_productType=1|5|6|7|9",
    "count": 8,
    "start": 0,
}

PRODUCTS_BATCH_PARAMS = {
    "c_method": "getPrices",
    "locale": "en-US",
}

GROUP_ATTRIBUTES_PARAMS = {
    "include": "available",
    "marketLocale": "en-US",
}

DOCUMENTS_PARAMS = {
    "marketLocale": "en-US",
}

# ==========================
# HEADERS
# ==========================
HEADERS = {
    "accept": "application/json",
    "origin": "https://www.jabra.com",
    "referer": "https://www.jabra.com/",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
    "x-dw-client-id": "6cc5db7b-65f3-430c-93e9-c71f9b48da61",
}

PARSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ==========================
# CRAWLER SETTINGS
# ==========================
BATCH_SIZE = 8
REQUEST_DELAY = 0.3  # seconds between batch requests
PARSER_TIMEOUT = 30  # seconds

# ==========================
# DOCUMENT FILTERS
# ==========================
ALLOWED_LANGUAGE = "en-us"
ALLOWED_DOCUMENT_TYPES = {
    "Technical Specifications",
    "User Manual",
    "Datasheet"
}

# ==========================
# PROXY (if needed)
# ==========================
PROXY = ""

# ==========================
# EXPORT SETTINGS
# ==========================
FILE_HEADERS = [
    "product_name",
    "product_url",
    "sku",
    "productId",
    "segmentType",
    "warranty",
    "model",
    "images",
    "selling_price",
    "regular_price",
    "currency",
    "documents",
    "section_title",
    "features",
]