from mongoengine import (
    DynamicDocument,
    StringField,
    IntField,
    FloatField,
    ListField,
)
from settings import (
    MONGO_COLLECTION_PRODUCT_URL,
    MONGO_COLLECTION_URL_FAILED,
    MONGO_COLLECTION_DATA,
    MONGO_COLLECTION_RESPONSE,
    MONGO_COLLECTION_CATEGORY,
)


class ProductItem(DynamicDocument):
    """Final product data fields (JSON-LD based)"""
    meta = {"db_alias": "default","collection": MONGO_COLLECTION_DATA}

    company_name = StringField()
    sku = StringField()
    product_title = StringField()
    brand = StringField()
    category = StringField()
    site_url = StringField()
    product_url = StringField()
    cost = FloatField()
    currency = StringField()
    product_cost_brand = FloatField()
    notes = StringField()
    battery_type = StringField()
    number_of_batteries = StringField()
    images = StringField()  


class ProductUrlItem(DynamicDocument):
    """Product URL fields (from category crawl)"""
    meta = {"db_alias": "default","collection": MONGO_COLLECTION_PRODUCT_URL}

    url = StringField(required=True)
    product_name = StringField()
    page_no = IntField()
    category_url = StringField()
    category_name = StringField()


class CategoryUrlItem(DynamicDocument):
    """Category URL fields"""
    meta = {"db_alias": "default","collection": MONGO_COLLECTION_CATEGORY}
    url = StringField(required=True)
    name = StringField()


class ProductResponseItem(DynamicDocument):
    """Response logging fields"""
    meta = {"db_alias": "default","collection": MONGO_COLLECTION_RESPONSE,}
    url = StringField(required=True)


class ProductFailedItem(DynamicDocument):
    """Failed URL fields"""
    meta = {"db_alias": "default","collection": MONGO_COLLECTION_URL_FAILED,}
    url = StringField(required=True)
