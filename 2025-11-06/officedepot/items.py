from mongoengine import DynamicDocument, StringField, BooleanField, DictField, ListField, IntField, FloatField
from settings import (
    MONGO_COLLECTION_PRODUCT_URL,
    MONGO_COLLECTION_URL_FAILED,
    MONGO_COLLECTION_DATA,
    MONGO_COLLECTION_RESPONSE, 
    MONGO_COLLECTION_CATEGORY,
    MONGO_COLLECTION_PAGINATION
)

class ProductItem(DynamicDocument):
    """Product data fields"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    
    company_name = StringField()
    manufacturer_name = StringField()
    brand_name = StringField()
    vendor_seller_part_number = StringField()
    item_name = StringField()
    full_product_description = StringField()
    price = StringField()
    unit_of_issue = StringField()
    qty_per_uoi = StringField()
    product_category = StringField()
    url = StringField()
    availability = StringField()
    manufacturer_part_number = StringField()
    country_of_origin = StringField()
    upc = StringField()
    model_number = StringField()


class ProductUrlItem(DynamicDocument):
    """Product URL fields"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PRODUCT_URL}
    url = StringField(required=True)
    product_name = StringField()
    page_no = IntField()
    category_url = StringField()
    category_name = StringField() 


class CategoryUrlItem(DynamicDocument):
    """Category URL fields"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    url = StringField(required=True)
    name = StringField()


class ProductResponseItem(DynamicDocument):
    """Response fields"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_RESPONSE}
    url = StringField(required=True)


class ProductFailedItem(DynamicDocument):
    """Failed URL fields"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)

