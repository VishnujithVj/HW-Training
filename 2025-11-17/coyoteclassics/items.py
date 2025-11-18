from mongoengine import (DynamicDocument,StringField,ListField,DateTimeField,IntField,)
import datetime
from settings import MONGO_COLLECTION_URL, MONGO_COLLECTION_DATA,MONGO_COLLECTION_URL_FAILED

class ProductItem(DynamicDocument):

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    source_link = StringField(required=True, unique=True)
    make = StringField()
    model = StringField()
    year = IntField()
    vin = StringField()
    price = StringField()
    mileage = StringField()
    transmission = StringField()
    engine = StringField()
    color = StringField()
    fuel_type = StringField()
    body_style = StringField()
    description = StringField()
    image_urls = ListField(StringField())


class ProductUrlItem(DynamicDocument):

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL}
    url = StringField(required=True, unique=True)
    category = StringField()
    category_url = StringField()  
    page_no = IntField()



class ProductFailedItem(DynamicDocument):

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
