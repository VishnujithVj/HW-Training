from datetime import datetime
import os
import calendar
import logging
import configparser
import pytz
from dateutil.relativedelta import relativedelta, MO
from mongoengine import connect


""" LOGGING CONFIGURATION """
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

""" BASIC PROJECT DETAILS """
PROJECT = "bipa"
CLIENT_NAME = "bipa"
PROJECT_NAME = "bipa"
FREQUENCY = ""
BASE_URL = "https://www.bipa.at"


""" DATE AND TIME VARIABLES """
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT_NAME}_{iteration}"

""" DATABASE CONFIGURATION """
MONGO_DB = f"{PROJECT_NAME}_db2"

MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category_urls"
MONGO_COLLECTION_URL = f"{PROJECT_NAME}_product_urls"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"
MONGO_COLLECTION_RESPONSE = f"{PROJECT_NAME}_response"
MONGO_COLLECTION_MISMATCH = f"{PROJECT_NAME}_mismatch"
MONGO_COLLECTION_EMPTY = f"{PROJECT_NAME}_empty"
MONGO_COLLECTION_COUNT = f"{PROJECT_NAME}_count"
MONGO_COLLECTION_PAGINATION = f"{PROJECT_NAME}_pagination"

""" MongoDB Connection """
connect(db=MONGO_DB, host=f"mongodb://localhost:27017/{MONGO_DB}", alias="default")

""" SHARD COLLECTION CONFIG """
MONGO_COL_URL = MONGO_COLLECTION_URL
SHARD_COLLECTION = [
    {"col": MONGO_COL_URL, "unique": True, "indexfield": "url"},
]

""" HEADERS AND NETWORK CONFIG """
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



""" PAGINATION CONFIGURATION """
PRODUCTS_PER_PAGE = 24


FILE_HEADERS = [
    "unique_id",
    "competitor_name",
    "store_name",
    "store_addressline1",
    "store_addressline2",
    "store_suburb",
    "store_state",
    "store_postcode",
    "store_addressid",
    "extraction_date",
    "product_name",
    "brand",
    "brand_type",
    "grammage_quantity",
    "grammage_unit",
    "drained_weight",
    "producthierarchy_level1",
    "producthierarchy_level2",
    "producthierarchy_level3",
    "producthierarchy_level4",
    "producthierarchy_level5",
    "producthierarchy_level6",
    "producthierarchy_level7",
    "regular_price",
    "selling_price",
    "price_was",
    "promotion_price",
    "promotion_valid_from",
    "promotion_valid_upto",
    "promotion_type",
    "percentage_discount",
    "promotion_description",
    "package_sizeof_sellingprice",
    "per_unit_sizedescription",
    "price_valid_from",
    "price_per_unit",
    "multi_buy_item_count",
    "multi_buy_items_price_total",
    "currency",
    "breadcrumb",
    "pdp_url",
    "variants",
    "product_description",
    "instructions",
    "storage_instructions",
    "preparationinstructions",
    "instructionforuse",
    "country_of_origin",
    "allergens",
    "age_of_the_product",
    "age_recommendations",
    "flavour",
    "nutritions",
    "nutritional_information",
    "vitamins",
    "labelling",
    "grade",
    "region",
    "packaging",
    "receipies",
    "processed_food",
    "barcode",
    "frozen",
    "chilled",
    "organictype",
    "cooking_part",
    "Handmade",
    "max_heating_temperature",
    "special_information",
    "label_information",
    "dimensions",
    "special_nutrition_purpose",
    "feeding_recommendation",
    "warranty",
    "color",
    "model_number",
    "material",
    "usp",
    "dosage_recommendation",
    "tasting_note",
    "food_preservation",
    "size",
    "rating",
    "review",
    "file_name_1",
    "image_url_1",
    "file_name_2",
    "image_url_2",
    "file_name_3",
    "image_url_3",
    "competitor_product_key",
    "fit_guide",
    "occasion",
    "material_composition",
    "style",
    "care_instructions",
    "heel_type",
    "heel_height",
    "upc",
    "features",
    "dietary_lifestyle",
    "manufacturer_address",
    "importer_address",
    "distributor_address",
    "vinification_details",
    "recycling_information",
    "return_address",
    "alchol_by_volume",
    "beer_deg",
    "netcontent",
    "netweight",
    "site_shown_uom",
    "ingredients",
    "random_weight_flag",
    "instock",
    "promo_limit",
    "product_unique_key",
    "multibuy_items_pricesingle",
    "perfect_match",
    "servings_per_pack",
    "Warning",
    "suitable_for",
    "standard_drinks",
    "environmental",
    "grape_variety",
    "retail_limit"
]
