from mongoengine import DynamicDocument, StringField, BooleanField, DictField, ListField, IntField, FloatField
from settings import  MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_URL, MONGO_COLLECTION_URL_FAILED, MONGO_COLLECTION_DATA, MONGO_COLLECTION_PAGINATION


class ProductItem(DynamicDocument):
    """Main product data"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}

    id = StringField()
    reference_number = StringField()
    url = StringField()
    broker_display_name = StringField()
    broker = StringField()
    category = StringField()
    category_url = StringField()
    title = StringField()
    description = StringField()
    location = StringField()
    price = StringField()
    currency = StringField()
    price_per = StringField()
    bedrooms = StringField()
    bathrooms = StringField()
    furnished = StringField()
    rera_permit_number = StringField()
    dtcm_licence = StringField()
    scraped_ts = StringField()
    amenities = ListField()
    details = DictField()
    agent_name = StringField()
    number_of_photos = IntField()
    user_id = StringField()
    phone_number = StringField()
    date = StringField()
    iteration_number = StringField()
    depth = IntField()
    property_type = StringField()
    sub_category_1 = StringField()
    sub_category_2 = StringField()
    published_at = StringField()


class ProductUrlItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL}
    url = StringField(required=True)


class ProductFailedItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)


class ProductCategoryUrlItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    url = StringField(required=True)


class ProductPageItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PAGINATION}
    url = StringField(required=True)
