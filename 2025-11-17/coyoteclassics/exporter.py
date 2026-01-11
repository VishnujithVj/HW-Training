import csv
import logging
from mongoengine import connect
from settings import CSV_FILE, FILE_HEADERS, MONGO_DB, MONGO_HOST
from items import ProductItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


def clean_price(price):
    """Convert $72,995 → 72.995"""
    if not price:
        return ""

    """remove $ and commas"""
    p = price.replace("$", "").replace(",", "").strip()

    if not p.isdigit():
        return ""

    """convert to integer"""
    num = int(p)

    """convert to European style thousands: 72000 → 72.000"""
    return f"{num:,}".replace(",", ".")


def clean_description(desc):
    """Remove newlines, fix spacing"""
    if not desc:
        return ""
    return " ".join(desc.replace("\n", " ").split())  


class Export:
    def __init__(self, filepath=CSV_FILE):
        connect(db=MONGO_DB, host=MONGO_HOST)
        self.filepath = filepath

    def start(self):
        logging.info("Exporting to CSV: %s", self.filepath)

        with open(self.filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(FILE_HEADERS)

            """export cars older than 1990"""
            for item in ProductItem.objects(year__lt=1990).no_cache():

                price_clean = clean_price(item.price)
                desc_clean = clean_description(item.description)
                images = "|".join(item.image_urls or [])

                row = [
                    item.source_link,
                    item.year or "",
                    item.make or "",
                    item.model or "",
                    item.vin or "",
                    price_clean,
                    item.mileage or "",
                    item.transmission or "",
                    item.engine or "",
                    item.color or "",
                    item.fuel_type or "",
                    item.body_style or "",
                    desc_clean,
                    images,
                ]

                writer.writerow(row)

        logging.info("Export complete. File saved: %s", self.filepath)


if __name__ == "__main__":
    exporter = Export()
    exporter.start()
