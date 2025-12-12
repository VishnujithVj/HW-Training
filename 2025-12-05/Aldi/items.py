from mongoengine import DynamicDocument, StringField, BooleanField, ListField, DictField

from settings import (
    MONGO_COLLECTION_CATEGORY,
    MONGO_COLLECTION_URLS,
    MONGO_COLLECTION_DATA,
    MONGO_COLLECTION_URL_FAILED,
    MONGO_COLLECTION_VARIANTS, 
)


class ProductCategoryItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    
    category_name = StringField(required=True)
    category_key = StringField(required=True)
    category_slug = StringField()
    subcategories = ListField(DictField())


class ProductUrlItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URLS}

    category = StringField(required=True)
    subcategory = StringField()
    product_name = StringField()
    product_url = StringField(required=True)
    sku = StringField(required=True)


class ProductItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}

    unique_id = StringField()
    competitor_name = StringField()
    store_name = StringField()
    extraction_date = StringField()
    product_name = StringField()
    brand = StringField()
    grammage_quantity = StringField()
    grammage_unit = StringField()
    producthierarchy_level1 = StringField()
    producthierarchy_level2 = StringField()
    producthierarchy_level3 = StringField()
    regular_price = StringField()
    selling_price = StringField()
    currency = StringField()
    breadcrumb = StringField()
    pdp_url = StringField()
    variants = StringField() 
    product_description = StringField()
    storage_instructions = StringField()
    country_of_origin = StringField()
    packaging = StringField()
    image_urls = ListField()
    competitor_product_key = StringField()
    alchol_by_volume = StringField()    
    site_shown_uom = StringField()
    ingredients = StringField()
    product_unique_key = StringField()


class ProductVariantItem(DynamicDocument):
    """NEW MODEL - Stores individual variant details"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_VARIANTS}

    parent_sku = StringField(required=True) 
    parent_name = StringField()
    parent_brand = StringField()
    variant_sku = StringField(required=True) 
    variant_name = StringField()
    variant_type = StringField()  
    variant_value = StringField()  
    pdp_url = StringField()
    brand = StringField()
    extraction_date = StringField()


class ProductFailedItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}

    url = StringField(required=True)
    reason = StringField()
    error_type = StringField()