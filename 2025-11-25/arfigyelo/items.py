from mongoengine import (
    DynamicDocument,
    StringField,
    ListField,
    DictField,
    DateTimeField,
    IntField,
)
from settings import (
    MONGO_COLLECTION_CATEGORY,
    MONGO_COLLECTION_DATA,
    MONGO_COLLECTION_URL_FAILED,
)


class ProductCategoryUrlItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}

    cat_id = IntField(required=True)
    url = StringField(required=True)
    name = StringField()
    path = StringField()
    parent = StringField()


class ProductItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}

    unique_id = StringField()
    competitor_name = StringField()
    extraction_date = DateTimeField()
    product_name = StringField()
    grammage_quantity = StringField()
    grammage_unit = StringField()
    selling_price = StringField()
    currency = StringField()
    product_description = ListField(DictField())  # list of {store, amount}
    packaging = StringField()
    image_url1 = StringField()
    image_url2 = StringField()
    competitor_product_key = StringField()
    site_shown_uom = StringField()
    product_unique_key = StringField()


class ProductFailedItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)
