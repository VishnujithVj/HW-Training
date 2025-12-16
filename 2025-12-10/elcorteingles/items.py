from mongoengine import DynamicDocument, StringField, BooleanField, DictField, ListField, IntField, FloatField
from settings import MONGO_COLLECTION_INPUT, MONGO_COLLECTION_MATCHED, MONGO_COLLECTION_DATA

class InputDetailsItem(DynamicDocument):
    """Input details with EAN and product name"""
    
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_INPUT}
    ean_master = StringField()
    product_general_name = StringField()


class MatchedProductItem(DynamicDocument):
    """Matched products from search""" 
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_MATCHED}

    match_type = StringField()
    ean = StringField()
    score = IntField()
    product_name = StringField()
    product_url = StringField(required=True)


class ProductDetailsItem(DynamicDocument):
    """Complete product details from PDP"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA} 
    
    product_name = StringField()
    product_url = StringField(required=True)
    brand = StringField()
    price = FloatField()
    breadcrumbs = StringField()
    images = ListField()
    description = StringField()
    model = StringField()
    reference = StringField()
    ean = StringField()
    additional_details = DictField()