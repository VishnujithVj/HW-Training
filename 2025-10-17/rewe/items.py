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
    store_addressline1 = StringField()
    store_addressline2 = StringField()
    store_suburb = StringField()
    store_state = StringField()
    store_postcode = StringField()
    store_addressid = StringField()
    extraction_date = DateTimeField(default=lambda: datetime.now) 
    product_name = StringField()
    brand = StringField()
    grammage_quantity = StringField()
    grammage_unit = StringField()
    
    producthierarchy_level1 = StringField()
    producthierarchy_level2 = StringField()
    producthierarchy_level3 = StringField()
    producthierarchy_level4 = StringField()
    producthierarchy_level5 = StringField()
    producthierarchy_level6 = StringField()
    producthierarchy_level7 = StringField()
    
    regular_price = StringField()
    selling_price = StringField()
    price_was = StringField()
    promotion_price = StringField()
    promotion_valid_upto = StringField()
    percentage_discount = StringField()
    promotion_description = StringField()
    price_per_unit = StringField()
    currency = StringField(default="EUR")
    
    breadcrumb = StringField()
    pdp_url = StringField()
    product_description = StringField()
    storage_instructions = StringField()
    preparationinstructions = StringField()
    instructionforuse = StringField()
    
    country_of_origin = StringField()
    allergens = StringField()
    nutritional_information = StringField()
    barcode = StringField()
    organictype = StringField()
    label_information = StringField()
    
    file_name_1 = StringField()
    image_url_1 = StringField()
    file_name_2 = StringField()
    image_url_2 = StringField()
    file_name_3 = StringField()
    image_url_3 = StringField()
    
    competitor_product_key = StringField()
    manufacturer_address = StringField()
    site_shown_uom = StringField()
    ingredients = StringField()
    instock = BooleanField(default=True)
    product_unique_key = StringField()


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