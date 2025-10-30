from mongoengine import DynamicDocument, StringField, BooleanField, DictField, ListField, IntField, FloatField, DateTimeField
from datetime import datetime, timezone
from settings import (
    MONGO_COL_URL, MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_EMPTY,
    MONGO_COLLECTION_URL_FAILED,
    MONGO_COLLECTION_DATA, MONGO_COLLECTION_MISMATCH,
    MONGO_COLLECTION_RESPONSE, MONGO_COLLECTION_PAGINATION
)


class ProductItem(DynamicDocument):
    """initializing Product fields and its Data-Types"""
    
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    
    unique_id = StringField(required=True, unique=True)
    competitor_name = StringField(default="REWE")
    store_name = StringField(default="REWE Online")
    extraction_date = DateTimeField(default=lambda: datetime.now(timezone.utc))
    
    product_name = StringField()
    brand = StringField()
    pdp_url = StringField()
    
    regular_price = StringField()
    selling_price = StringField()
    currency = StringField(default="EUR")
    percentage_discount = StringField()
    promotion_valid_upto = StringField()
    
    grammage_quantity = StringField()
    grammage_unit = StringField()
    country_of_origin = StringField()
    barcode = StringField()
    nutritions = StringField()
    ingredients = StringField()
    
    image_url_1 = StringField()
    image_url_2 = StringField()
    image_url_3 = StringField()
    
    instock = BooleanField(default=True)
    review_dict_list = ListField()
    brand_type = StringField()
    drained_weight = StringField()
    producthierarchy_level1 = StringField()
    producthierarchy_level2 = StringField()
    producthierarchy_level3 = StringField()
    producthierarchy_level4 = StringField()
    producthierarchy_level5 = StringField()
    producthierarchy_level6 = StringField()
    producthierarchy_level7 = StringField()
    price_was = StringField()
    promotion_price = StringField()
    promotion_valid_from = StringField()
    promotion_type = StringField()
    promotion_description = StringField()
    package_sizeof_sellingprice = StringField()
    per_unit_sizedescription = StringField()
    price_valid_from = StringField()
    price_per_unit = StringField()
    multi_buy_item_count = StringField()
    multi_buy_items_price_total = StringField()
    breadcrumb = StringField()
    variants = StringField()
    product_description = StringField()
    instructions = StringField()
    storage_instructions = StringField()
    preparationinstructions = StringField()
    instructionforuse = StringField()
    allergens = StringField()
    age_of_the_product = StringField()
    age_recommendations = StringField()
    flavour = StringField()
    nutritional_information = StringField()
    vitamins = StringField()
    labelling = StringField()
    grade = StringField()
    region = StringField()
    packaging = StringField()
    receipies = StringField()
    processed_food = StringField()
    frozen = StringField()
    chilled = StringField()
    organictype = StringField()
    cooking_part = StringField()
    Handmade = StringField()
    max_heating_temperature = StringField()
    special_information = StringField()
    label_information = StringField()
    dimensions = StringField()
    special_nutrition_purpose = StringField()
    feeding_recommendation = StringField()
    warranty = StringField()
    color = StringField()
    model_number = StringField()
    material = StringField()
    usp = StringField()
    dosage_recommendation = StringField()
    tasting_note = StringField()
    food_preservation = StringField()
    size = StringField()
    rating = StringField()
    review = StringField()
    file_name_1 = StringField()
    file_name_2 = StringField()
    file_name_3 = StringField()
    competitor_product_key = StringField()
    fit_guide = StringField()
    occasion = StringField()
    material_composition = StringField()
    style = StringField()
    care_instructions = StringField()
    heel_type = StringField()
    heel_height = StringField()
    upc = StringField()
    features = StringField()
    dietary_lifestyle = StringField()
    manufacturer_address = StringField()
    importer_address = StringField()
    distributor_address = StringField()
    vinification_details = StringField()
    recycling_information = StringField()
    return_address = StringField()
    alchol_by_volume = StringField()
    beer_deg = StringField()
    netcontent = StringField()
    netweight = StringField()
    site_shown_uom = StringField()
    random_weight_flag = StringField()
    promo_limit = StringField()
    product_unique_key = StringField()
    multibuy_items_pricesingle = StringField()
    perfect_match = StringField()
    servings_per_pack = StringField()
    Warning = StringField()
    suitable_for = StringField()
    standard_drinks = StringField()
    grape_variety = StringField()
    retail_limit = StringField()


class ProductUrlItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COL_URL}
    url = StringField(required=True)
    category_url = StringField()
    subcategory_url = StringField()


class ProductFailedItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)


class ProductMismatchItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_MISMATCH}
    input_style = StringField(required=True)


class ProductEmptyItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_EMPTY}
    input_style = StringField(required=True)


class ProductResponseItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_RESPONSE}
    url = StringField(required=True)


class ProductCategoryUrlItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    url = StringField(required=True)


class ProductPageItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PAGINATION}
    url = StringField(required=True)