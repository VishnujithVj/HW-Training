from mongoengine import DynamicDocument, StringField, BooleanField, DateTimeField
from datetime import datetime, timezone
# from settings import (
#     MONGO_COL_URL, MONGO_COLLECTION_EMPTY,
#     MONGO_COLLECTION_URL_FAILED, MONGO_COLLECTION_DATA,
#     MONGO_COLLECTION_MISMATCH, MONGO_COLLECTION_RESPONSE,
#     MONGO_COLLECTION_IMAGES, MONGO_COLLECTION_CATEGORY,
#     MONGO_COLLECTION_STORE_CODE, MONGO_COLLECTION_COUNT,
#     MONGO_COLLECTION_PAGINATION
# )


class CategoryUrlItem(DynamicDocument):
    """Initializing Category URL fields and their Data-Types"""

    url = StringField(required=True)
    name = StringField()
    parent_url = StringField()
    level = StringField()
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))

    # meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    meta = {"collection": "category_urls", "db_alias": "default"}


class ProductUrlItem(DynamicDocument):
    """Initializing Product URL fields and their Data-Types"""

    url = StringField(required=True)
    category_url = StringField()
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))

    # meta = {"db_alias": "default", "collection": MONGO_COL_URL}
    meta = {"collection": "product_urls", "db_alias": "default"}


class ProductItem(DynamicDocument):
    """Initializing Product Data fields and their Data-Types"""

    unique_id = StringField(required=True, unique=True)
    competitor_name = StringField(default="BIPA")
    store_name = StringField(default="BIPA Online")
    store_addressline1 = StringField(default="")
    store_addressline2 = StringField(default="")
    store_suburb = StringField(default="")
    store_state = StringField(default="")
    store_postcode = StringField(default="")
    store_addressid = StringField(default="")
    extraction_date = DateTimeField(default=lambda: datetime.now(timezone.utc))

    product_name = StringField(default="")
    brand = StringField(default="")
    brand_type = StringField(default="")
    grammage_quantity = StringField(default="")
    grammage_unit = StringField(default="")
    drained_weight = StringField(default="")

    producthierarchy_level1 = StringField(default="")
    producthierarchy_level2 = StringField(default="")
    producthierarchy_level3 = StringField(default="")
    producthierarchy_level4 = StringField(default="")
    producthierarchy_level5 = StringField(default="")
    producthierarchy_level6 = StringField(default="")
    producthierarchy_level7 = StringField(default="")

    regular_price = StringField(default="")
    selling_price = StringField(default="")
    price_was = StringField(default="")
    promotion_price = StringField(default="")
    promotion_valid_from = StringField(default="")
    promotion_valid_upto = StringField(default="")
    promotion_type = StringField(default="")
    percentage_discount = StringField(default="")
    promotion_description = StringField(default="")
    package_sizeof_sellingprice = StringField(default="")
    per_unit_sizedescription = StringField(default="")
    price_valid_from = StringField(default="")
    price_per_unit = StringField(default="")
    multi_buy_item_count = StringField(default="")
    multi_buy_items_price_total = StringField(default="")
    currency = StringField(default="EUR")

    breadcrumb = StringField(default="")
    pdp_url = StringField(default="")
    variants = StringField(default="")
    product_description = StringField(default="")
    instructions = StringField(default="")
    storage_instructions = StringField(default="")
    preparationinstructions = StringField(default="")
    instructionforuse = StringField(default="")
    country_of_origin = StringField(default="")
    allergens = StringField(default="")
    age_of_the_product = StringField(default="")
    age_recommendations = StringField(default="")
    flavour = StringField(default="")
    nutritions = StringField(default="")
    nutritional_information = StringField(default="")
    vitamins = StringField(default="")
    labelling = StringField(default="")
    grade = StringField(default="")
    region = StringField(default="")
    packaging = StringField(default="")
    receipies = StringField(default="")
    processed_food = StringField(default="")
    barcode = StringField(default="")
    frozen = StringField(default="")
    chilled = StringField(default="")
    organictype = StringField(default="")
    cooking_part = StringField(default="")
    Handmade = StringField(default="")
    max_heating_temperature = StringField(default="")
    special_information = StringField(default="")
    label_information = StringField(default="")
    dimensions = StringField(default="")
    special_nutrition_purpose = StringField(default="")
    feeding_recommendation = StringField(default="")
    warranty = StringField(default="")
    color = StringField(default="")
    model_number = StringField(default="")
    material = StringField(default="")
    usp = StringField(default="")
    dosage_recommendation = StringField(default="")
    tasting_note = StringField(default="")
    food_preservation = StringField(default="")
    size = StringField(default="")
    rating = StringField(default="")
    review = StringField(default="")

    file_name_1 = StringField(default="")
    image_url_1 = StringField(default="")
    file_name_2 = StringField(default="")
    image_url_2 = StringField(default="")
    file_name_3 = StringField(default="")
    image_url_3 = StringField(default="")

    competitor_product_key = StringField(default="")
    fit_guide = StringField(default="")
    occasion = StringField(default="")
    material_composition = StringField(default="")
    style = StringField(default="")
    care_instructions = StringField(default="")
    heel_type = StringField(default="")
    heel_height = StringField(default="")
    upc = StringField(default="")
    features = StringField(default="")
    dietary_lifestyle = StringField(default="")
    manufacturer_address = StringField(default="")
    importer_address = StringField(default="")
    distributor_address = StringField(default="")
    vinification_details = StringField(default="")
    recycling_information = StringField(default="")
    return_address = StringField(default="")
    alchol_by_volume = StringField(default="")
    beer_deg = StringField(default="")
    netcontent = StringField(default="")
    netweight = StringField(default="")
    site_shown_uom = StringField(default="")
    ingredients = StringField(default="")
    random_weight_flag = StringField(default="")
    instock = BooleanField(default=True)
    promo_limit = StringField(default="")
    product_unique_key = StringField(default="")
    multibuy_items_pricesingle = StringField(default="")
    perfect_match = StringField(default="")
    servings_per_pack = StringField(default="")
    Warning = StringField(default="")
    suitable_for = StringField(default="")
    standard_drinks = StringField(default="")
    grape_variety = StringField(default="")
    retail_limit = StringField(default="")

    # meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    meta = {"collection": "product_data", "db_alias": "default"}


class ProductFailedItem(DynamicDocument):
    """Initializing Failed URL fields and their Data-Types"""

    url = StringField(required=True)
    # meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    meta = {"collection": "product_failed_urls", "db_alias": "default"}


class ProductEmptyItem(DynamicDocument):
    """Initializing Empty URL fields and their Data-Types"""

    input_style = StringField(required=True)
    # meta = {"db_alias": "default", "collection": MONGO_COLLECTION_EMPTY}
    meta = {"collection": "product_empty", "db_alias": "default"}


class ProductMismatchItem(DynamicDocument):
    """Initializing Mismatch fields and their Data-Types"""

    input_style = StringField(required=True)
    # meta = {"db_alias": "default", "collection": MONGO_COLLECTION_MISMATCH}
    meta = {"collection": "product_mismatch", "db_alias": "default"}


class ProductCountItem(DynamicDocument):
    """Initializing Count fields and their Data-Types"""

    zipcode = StringField(required=True)
    # meta = {"db_alias": "default", "collection": MONGO_COLLECTION_COUNT}
    meta = {"collection": "product_count", "db_alias": "default"}


class ProductResponseItem(DynamicDocument):
    """Initializing Response fields and their Data-Types"""

    url = StringField(required=True)
    # meta = {"db_alias": "default", "collection": MONGO_COLLECTION_RESPONSE}
    meta = {"collection": "product_response", "db_alias": "default"}


class ProductPageItem(DynamicDocument):
    """Initializing Pagination URL fields and their Data-Types"""

    url = StringField(required=True)
    # meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PAGINATION}
    meta = {"collection": "product_pagination", "db_alias": "default"}
