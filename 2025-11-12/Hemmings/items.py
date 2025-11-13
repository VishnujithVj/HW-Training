from mongoengine import DynamicDocument, StringField, FloatField, IntField, ListField, BooleanField
from settings import MONGO_COLLECTION_URL, MONGO_COLLECTION_DATA, MONGO_COLLECTION_FAILED


class ProductUrlItem(DynamicDocument):
    """Store product URLs to crawl"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL}
    url = StringField(required=True, unique=True)


class ProductItem(DynamicDocument):
    """Store parsed product (car) details"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    make = StringField()
    model = StringField()
    year = IntField()
    vin = StringField()
    price = FloatField()
    mileage = StringField()
    transmission = StringField()
    engine = StringField()
    color = StringField()
    fuel_type = StringField()
    body_style = StringField()
    description = StringField()
    image_urls = ListField(StringField())
    source_url = StringField()


class ProductFailedItem(DynamicDocument):
    """Store failed URLs"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_FAILED}
    url = StringField(required=True, unique=True)
    reason = StringField()
