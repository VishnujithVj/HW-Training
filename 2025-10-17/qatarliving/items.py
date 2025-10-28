from mongoengine import DynamicDocument, StringField, BooleanField, DictField, ListField, IntField, FloatField, DateTimeField
import datetime
from settings import (
    MONGO_COL_URL, 
    MONGO_COLLECTION_URL_FAILED,
    MONGO_COLLECTION_DATA, 
    MONGO_COLLECTION_RESPONSE, 
    MONGO_COLLECTION_CATEGORY
)


class ProductItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    url = StringField()
    product_name = StringField()
    brand = StringField()
    currency = StringField()
    review_dict_list = ListField()


class ProductUrlItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COL_URL}
    url = StringField(required=True)


class ProductCategoryUrlItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    url = StringField(required=True)
    category_id = IntField(required=True)

class ProductFailedItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)


class QatarLivingPropertyItem(DynamicDocument):
    """Qatar Living Properties data item"""
    
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    unique_id = StringField(required=True)
    url = StringField(required=True)
    title = StringField()
    price = StringField()
    bedroom = StringField()
    bathroom = StringField()
    furnishing = StringField()
    property_type = StringField()
    square_meters = StringField()
    country = StringField()
    city = StringField()
    agent_name = StringField()
    company = StringField()
    images = ListField()
    category_id = IntField()
    timestamp = DateTimeField(default=datetime.datetime.utcnow)


# Keep other classes commented or remove them since they're not used
# class ProductMismatchItem(DynamicDocument):
#     """initializing URL fields and its Data-Types"""

#     #meta = {"db_alias": "default", "collection": MONGO_COLLECTION_MISMATCH}
#     input_style = StringField(required=True)


# class ProductEmptyItem(DynamicDocument):
#     """initializing URL fields and its Data-Types"""

#     #meta = {"db_alias": "default", "collection": MONGO_COLLECTION_EMPTY}
#     input_style = StringField(required=True)


# class ProductCountItem(DynamicDocument):
#     """initializing URL fields and its Data-Types"""

#     #meta = {"db_alias": "default", "collection": MONGO_COLLECTION_COUNT}
#     zipcode = StringField(required=True)


# class ProductResponseItem(DynamicDocument):
#     """initializing URL fields and its Data-Types"""

#     #meta = {"db_alias": "default", "collection": MONGO_COLLECTION_RESPONSE}
#     url = StringField(required=True)


# class ProductPageItem(DynamicDocument):
#     """initializing URL fields and its Data-Types"""

#     #meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PAGINATION}
#     url = StringField(required=True)