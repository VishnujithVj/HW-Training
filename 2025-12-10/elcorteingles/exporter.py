import csv
import logging
from pymongo import MongoClient
from settings import (
    MONGO_URI, MONGO_DB,
    MONGO_COLLECTION_DATA, FILE_NAME
)


# CSV File Headers
FILE_HEADERS = [
    "product_name",
    "product_url",
    "brand",
    "price",
    "breadcrumbs",
    "images",
    "description",
    "model",
    "reference",
    "ean",
    "additional_details"
]


class Export:
    """Post-Processing and CSV Export"""

    def __init__(self, writer):
        """Initialize MongoDB connection and CSV writer"""
        self.client = MongoClient(MONGO_URI)
        self.mongo = self.client[MONGO_DB]
        self.writer = writer
        logging.info("Exporter initialized with MongoDB connection")

    def start(self):
        """Export as CSV file"""
        # Write headers
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV Headers: {FILE_HEADERS}")
        
        # Fetch and process all items
        total_count = self.db[MONGO_COLLECTION_DATA].count_documents({})
        logging.info(f"Found {total_count} products to export")
        
        for idx, item in enumerate(self.db[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True), 1):
            # Extract fields and convert to string, replace None/null with empty string
            product_name = str(item.get("product_name", "")).strip() if item.get("product_name") else ""
            product_url = str(item.get("product_url", "")).strip() if item.get("product_url") else ""
            brand = str(item.get("brand", "")).strip() if item.get("brand") else ""
            price = str(item.get("price", "")).strip() if item.get("price") else ""
            breadcrumbs = str(item.get("breadcrumbs", "")).strip() if item.get("breadcrumbs") else ""
            
            # Handle images list
            images = item.get("images", [])
            if images and isinstance(images, list):
                images = "|".join([str(img).strip() for img in images if img])
            else:
                images = ""
            
            description = str(item.get("description", "")).strip() if item.get("description") else ""
            model = str(item.get("model", "")).strip() if item.get("model") else ""
            reference = str(item.get("reference", "")).strip() if item.get("reference") else ""
            ean = str(item.get("ean", "")).strip() if item.get("ean") else ""
            
            # Handle additional_details dict
            additional_details = item.get("additional_details", {})
            if additional_details and isinstance(additional_details, dict):
                # Convert dict to string format: key1:value1|key2:value2
                details_list = [f"{k}:{v}" for k, v in additional_details.items() if k and v]
                additional_details = "|".join(details_list)
            else:
                additional_details = ""
            
            # Prepare data row
            data = [
                product_name,
                product_url,
                brand,
                price,
                breadcrumbs,
                images,
                description,
                model,
                reference,
                ean,
                additional_details
            ]
            
            # Write to CSV
            self.writer.writerow(data)
            
            if idx % 100 == 0:
                logging.info(f"Exported {idx}/{total_count} products")
        
        logging.info(f"Export completed! Total products exported: {total_count}")

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed")


if __name__ == "__main__":
    csv_filename = f"{FILE_NAME}.csv"
    
    with open(csv_filename, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        export = Export(writer_file)
        export.start()
        export.close()
        file.close()
        
        logging.info(f"CSV file saved: {csv_filename}")