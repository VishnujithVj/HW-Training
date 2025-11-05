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

PROJECT = "FatFace"
CLIENT_NAME = "FatFace"
PROJECT_NAME = "fatface"
FREQUENCY = ""
BASE_URL = "https://www.fatface.com/"
API_URL = "https://www.fatface.com/headerstatic/seo-content"

datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"fatface_{iteration}"

MONGO_DB = f"fatface_db"
MONGO_COLLECTION_RESPONSE = f"{PROJECT_NAME}_response"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category_url"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"
MONGO_COLLECTION_PRODUCT_URL = f"{PROJECT_NAME}_product_url"


HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "accept": "application/json",
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}


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