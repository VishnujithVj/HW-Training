from mongoengine import (
    DynamicDocument, StringField, BooleanField, DictField,
    ListField, IntField, FloatField
)
from settings import (
MONGO_COLLECTION_DATA, MONGO_COLLECTION_POST_URL,
MONGO_COLLECTION_POST_ITEM, MONGO_COLLECTION_URL,
MONGO_COLLECTION_URL_FAILED, MONGO_COLLECTION_CATEGORY,
MONGO_COLLECTION_PAGINATION
)


class PropertyItem(DynamicDocument):
    """Stores final real-estate property data"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}

    reference_number = StringField()
    property_id = StringField()
    url = StringField()
    broker_display_name = StringField()
    category_name = StringField()
    title = StringField()
    property_type = StringField()
    depth = StringField()
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
    amenities = ListField(StringField())
    number_of_photos = IntField()
    phone_number = StringField()

class PropertyPostUrlItem(DynamicDocument):
    """Stores all post URLs collected for each tag"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_POST_URL}
    url = StringField(required=True)
    tag = StringField()
    title = StringField()
    update_date = IntField()


class PropertyPostItem(DynamicDocument):
    """Raw Haraj post extracted from HTML"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_POST_ITEM}
    url = StringField()
    dealapp_ad_id = StringField()
    dealapp_api_url = StringField()


class PropertyUrlItem(DynamicDocument):
    """Stores all URL entries"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL}
    url = StringField(required=True)

class PropertyFailedItem(DynamicDocument):
    """Failed URL storage"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)

class PropertyCategoryItem(DynamicDocument):
    """Stores category or subcategory URLs"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    url = StringField(required=True)

class PropertyPageItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PAGINATION}
    url = StringField(required=True)
