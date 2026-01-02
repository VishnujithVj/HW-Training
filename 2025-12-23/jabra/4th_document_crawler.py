import logging
import requests
from pymongo import MongoClient
from settings import (
    DOCUMENTS_URL, DOCUMENTS_PARAMS, HEADERS, BASE_URL,
    MONGO_URI, MONGO_DB, MONGO_COLLECTION_PRODUCT_DETAILS,
    MONGO_COLLECTION_DOCUMENTS, ALLOWED_LANGUAGE, ALLOWED_DOCUMENT_TYPES
)


class JabraDocumentsCrawler:
    """Crawling Product Documents from Jabra API"""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DB]

        self.source_col = self.db[MONGO_COLLECTION_PRODUCT_DETAILS]
        self.target_col = self.db[MONGO_COLLECTION_DOCUMENTS]

        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        logging.info("Documents Crawler initialized")

    def start(self):
        """Start crawling documents"""
        
        # Fetch products with group IDs
        products = self.source_col.find(
            {
                "groupId": {"$exists": True},
                "sku": {"$exists": True},
                "pageUrl": {"$exists": True}
            },
            {
                "groupId": 1,
                "productName": 1,
                "sku": 1,
                "pageUrl": 1
            }
        )

        for product in products:
            group_id = str(product.get("groupId"))
            sku = product.get("sku")
            product_name = product.get("productName")
            page_url = product.get("pageUrl")

            if not group_id or not sku or not page_url:
                continue

            api_url = DOCUMENTS_URL.format(group_id=group_id)
            params = DOCUMENTS_PARAMS.copy()

            product_url = f"{BASE_URL.rstrip('/')}{page_url}/buy?sku={sku}"

            logging.info(f"Fetching documents | groupId={group_id} | SKU={sku}")

            try:
                response = self.session.get(api_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                self.parse_item(
                    data=data,
                    group_id=group_id,
                    sku=sku,
                    product_name=product_name,
                    product_url=product_url
                )

            except Exception as e:
                logging.error(f"Failed groupId={group_id} | {e}")

    def parse_item(self, data, group_id, sku, product_name, product_url):
        """Parse and save document items"""
        
        if not isinstance(data, list):
            return

        for doc in data:
            language = doc.get("languageCode", "").lower()
            doc_type = doc.get("documentType")

            # Filter by language
            if language != ALLOWED_LANGUAGE:
                continue

            # Filter by document type
            if doc_type not in ALLOWED_DOCUMENT_TYPES:
                continue

            item = {
                "groupId": group_id,
                "sku": sku,
                "productName": product_name,
                "product_url": product_url,
                "documentType": doc.get("documentType"),
                "documentTypeTranslation": doc.get("documentTypeTranslation"),
                "fileType": doc.get("fileType"),
                "fileSize": doc.get("fileSize"),
                "fileUrl": doc.get("fileUrl"),
                "languageCode": doc.get("languageCode"),
                "languageTitle": doc.get("languageTitle"),
            }

            try:
                self.target_col.insert_one(item)
                logging.info(f"Saved document | {doc_type} | {product_name}")
            except Exception as e:
                logging.error(f"Failed to save document for {sku}: {e}")

    def stop(self):
        """Close MongoDB connection"""
        self.mongo.close()
        logging.info("Documents Crawler finished & MongoDB closed")


if __name__ == "__main__":
    crawler = JabraDocumentsCrawler()
    crawler.start()
    crawler.stop()