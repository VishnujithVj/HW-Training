import csv
import logging
from time import sleep
from mongoengine import connect
from settings import FILE_NAME, MONGO_DB


class Export:
    """Post-Processing"""

    def __init__(self, writer):
        self.writer = writer
        self.initialize_mongo_connection()

    def initialize_mongo_connection(self):
        """Initialize MongoDB connection for MongoEngine"""
        
        connect(db=MONGO_DB, alias='default', host='mongodb://localhost:27017/')
        logging.info(f"MongoDB connected to database: {MONGO_DB}")
        return True

    def start(self):
        """Export as CSV file"""

        # Define CSV headers
        FILE_HEADERS = [
            "unique_id", "url", "title", "price", "bedroom", "bathroom", 
            "furnishing", "property_type", "square_meters", "country", 
            "city", "agent_name", "company", "images", "category_id", "timestamp"
        ]
        
        self.writer.writerow(FILE_HEADERS)
        logging.info("CSV headers written")


        from items import QatarLivingPropertyItem
        items = QatarLivingPropertyItem.objects()
        
        item_count = 0
        for item in items:
            unique_id = item.unique_id or ""
            url = item.url or ""
            title = item.title or ""
            price = item.price or ""
            bedroom = item.bedroom or ""
            bathroom = item.bathroom or ""
            furnishing = item.furnishing or ""
            property_type = item.property_type or ""
            square_meters = item.square_meters or ""
            country = item.country or ""
            city = item.city or ""
            agent_name = item.agent_name or ""
            company = item.company or ""
            images = "|".join(item.images or [])
            category_id = str(item.category_id) if item.category_id else ""
            timestamp = item.timestamp.strftime("%Y-%m-%d %H:%M:%S") if item.timestamp else ""

            data = [
                unique_id,
                url,
                title,
                price,
                bedroom,
                bathroom,
                furnishing,
                property_type,
                square_meters,
                country,
                city,
                agent_name,
                company,
                images,
                category_id,
                timestamp
            ]

            self.writer.writerow(data)
            item_count += 1
            if item_count % 100 == 0:  
                logging.info(f"Exported {item_count} items...")

        logging.info(f"Export completed. Total items exported: {item_count}")


if __name__ == "__main__":
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
        file.close()