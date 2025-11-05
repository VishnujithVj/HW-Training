import csv
import logging
from mongoengine import connect
from settings import FILE_NAME, FILE_HEADERS, MONGO_DB
from items import ProductItem


# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# MongoDB Connection
connect(db=MONGO_DB, host=f"mongodb://localhost:27017/{MONGO_DB}", alias="default")


class Export:
    """Post-Processing: Export MongoEngine ProductItem to CSV"""

    def __init__(self, writer):
        self.writer = writer

    def start(self):
        """Export as CSV file"""

        # Write headers
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV Header written: {FILE_HEADERS}")

        # Iterate over products
        for item in ProductItem.objects():
        
            pdp_url = item.pdp_url or ""
            unique_id = item.unique_id or ""
            product_name = item.product_name or ""
            brand = item.brand or ""
            brand_type = item.brand_type or ""
            selling_price = item.selling_price or ""
            regular_price = item.regular_price or ""
            price_was = item.price_was or ""
            promotion_price = item.promotion_price or ""
            promotion_type = item.promotion_type or ""
            percentage_discount = item.percentage_discount or ""
            promotion_description = item.promotion_description or ""
            currency = item.currency or "EUR"
            product_description = item.product_description or ""
            producthierarchy_level1 = item.producthierarchy_level1 or ""
            producthierarchy_level2 = item.producthierarchy_level2 or ""
            producthierarchy_level3 = item.producthierarchy_level3 or ""
            producthierarchy_level4 = item.producthierarchy_level4 or ""
            producthierarchy_level5 = item.producthierarchy_level5 or ""
            producthierarchy_level6 = item.producthierarchy_level6 or ""
            producthierarchy_level7 = item.producthierarchy_level7 or ""
            image_url_1 = item.image_url_1 or ""
            image_url_2 = item.image_url_2 or ""
            image_url_3 = item.image_url_3 or ""
            breadcrumbs = item.breadcrumbs or ""
            instock = item.instock if item.instock is not None else True
            extraction_date = item.extraction_date.strftime("%Y-%m-%d %H:%M:%S") if item.extraction_date else ""


            # all extracted variables into a data list
            data = [
                pdp_url,
                unique_id,
                product_name,
                brand,
                brand_type,
                selling_price,
                regular_price,
                price_was,
                promotion_price,
                promotion_type,
                percentage_discount,
                promotion_description,
                currency,
                product_description,
                producthierarchy_level1,
                producthierarchy_level2,
                producthierarchy_level3,
                producthierarchy_level4,
                producthierarchy_level5,
                producthierarchy_level6,
                producthierarchy_level7,
                image_url_1,
                image_url_2,
                image_url_3,
                breadcrumbs,
                instock,
                extraction_date,
            ]

            # Write the row
            self.writer.writerow(data)

        logging.info(f"Export completed. CSV file saved as: {FILE_NAME}.csv")


# Entry Point
if __name__ == "__main__":
    import os
    os.makedirs("exports", exist_ok=True)
    file_path = f"exports/{FILE_NAME}.csv"

    with open(file_path, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter="|", quotechar='"')
        exporter = Export(writer_file)
        exporter.start()
