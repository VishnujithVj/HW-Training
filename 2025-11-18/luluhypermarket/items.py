from mongoengine import (
    DynamicDocument, StringField, BooleanField, DictField,
    ListField, IntField, FloatField
)

from settings import (
    MONGO_COLLECTION_URL,
    MONGO_COLLECTION_CATEGORY,
    MONGO_COLLECTION_URL_FAILED,
    MONGO_COLLECTION_DATA,
    MONGO_COLLECTION_RESPONSE,
)


class ProductCategoryUrlItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}

    url = StringField(required=True)
    label = StringField()
    level = StringField()

class ProductUrlItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL}
    url = StringField(required=True)


class ProductItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    product_id = StringField()
    url = StringField()
    product_name = StringField()
    product_color = StringField()
    material = StringField()
    quantity = StringField()
    details_string = StringField()
    specification = DictField()
    product_type = StringField()
    price = StringField()
    wasPrice = StringField()
    breadcrumb = StringField()
    stock = BooleanField()
    image = ListField()


class ProductFailedItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)
    reason = StringField()


class ProductResponseItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_RESPONSE}
    url = StringField(required=True)
