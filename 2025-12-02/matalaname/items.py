from mongoengine import DynamicDocument, StringField, ListField, BooleanField, FloatField, IntField, DictField
from settings import  MONGO_COLLECTION_URL_FAILED,MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_PLP, MONGO_COLLECTION_PDP

class CategoryItem(DynamicDocument):
    meta = {"collection": MONGO_COLLECTION_CATEGORY}
    category_name = StringField()
    sub_category_name = StringField()
    sub_category_url = StringField()
    uids = ListField(StringField())

class ProductItem(DynamicDocument):
    meta = {"collection": MONGO_COLLECTION_PLP}
    unique_id = IntField()
    url_key = StringField()
    product_name = StringField()
    selling_price = FloatField()
    regular_price = FloatField()
    currency=StringField()
    image_url = StringField()
    breadcrumbs = StringField()

class ProductDetailItem(DynamicDocument):
    meta = {"collection": MONGO_COLLECTION_PDP}

    unique_id = IntField()
    url = StringField()
    product_name = StringField()
    product_details = DictField()
    color=StringField()
    size=StringField()
    selling_price = FloatField()
    regular_price = FloatField()
    image = StringField()
    description = StringField()
    currency = StringField()
    gender= StringField()
    breadcrumbs = StringField()
    extraction_date = StringField()


class ProductFailedItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)