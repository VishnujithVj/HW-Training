from mongoengine import DynamicDocument, StringField, IntField, FloatField, ListField, DictField


class ProductIdItem(DynamicDocument):
    """Product IDs from initial search"""
    
    meta = {"db_alias": "default", "collection": "product_ids"}
    product_id = StringField(required=True)
    product_name = StringField()
    price = FloatField()
    price_per_unit = FloatField()
    currency = StringField()


class GroupIdItem(DynamicDocument):
    """Group IDs with pricing information"""
    
    meta = {"db_alias": "default", "collection": "group_ids"}
    sku = StringField(required=True)
    c_discountedPrice = FloatField()
    c_listedPrice = FloatField()
    c_discountPercentage = FloatField()
    c_pimFamilyId = StringField()
    c_pimGroupId = StringField()
    c_portfolio = StringField()
    c_productId = StringField()
    currency = StringField()


class ProductDetailsItem(DynamicDocument):
    """Detailed product information"""
    
    meta = {"db_alias": "default", "collection": "product_details"}
    groupId = StringField()
    familyId = StringField()
    familyName = StringField()
    productId = StringField()
    productName = StringField()
    sku = StringField(required=True)
    segmentType = StringField()
    warranty = StringField()
    pageUrl = StringField()
    supportPageUrl = StringField()
    model = StringField()
    groupState = StringField()
    hasBluetoothPairingGuide = StringField()
    attributes = DictField()
    images = ListField()


class ProductUrlItem(DynamicDocument):
    """Product URLs for parsing"""
    
    meta = {"db_alias": "default", "collection": "product_urls"}
    product_name = StringField()
    product_url = StringField(required=True)
    sku = StringField(required=True)


class DocumentItem(DynamicDocument):
    """Product documents (manuals, datasheets, etc.)"""
    
    meta = {"db_alias": "default", "collection": "documents"}
    groupId = StringField()
    sku = StringField(required=True)
    productName = StringField()
    product_url = StringField()
    documentType = StringField()
    documentTypeTranslation = StringField()
    fileType = StringField()
    fileSize = IntField()
    fileUrl = StringField()
    languageCode = StringField()
    languageTitle = StringField()


class ProductDataItem(DynamicDocument):
    """Final parsed product data"""
    
    meta = {"db_alias": "default", "collection": "product_data"}
    product_name = StringField()
    product_url = StringField(required=True)
    sku = StringField(required=True)
    productId = StringField()
    segmentType = StringField()
    warranty = StringField()
    model = StringField()
    images = ListField()
    selling_price = FloatField()
    regular_price = FloatField()
    currency = StringField()
    documents = ListField()
    section_title = StringField()
    features = ListField()