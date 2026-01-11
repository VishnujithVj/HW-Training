import csv
import logging
from mongoengine import connect
from items import ProductItem
from settings import MONGO_DB, MONGO_HOST, FILE_NAME, File_Headers


class Export:

    def __init__(self, writer):
        self.mongo = connect(db=MONGO_DB, host=MONGO_HOST)
        self.writer = writer
        logging.info("MongoDB connected")

    def start(self):

        self.writer.writerow(File_Headers)

        for item in ProductItem.objects():
            row = [
                item.product_id,
                item.url,
                item.product_name,
                item.product_color,
                item.material,
                item.quantity,
                item.details_string,
                str(item.specification),
                item.product_type,
                item.price,
                item.wasPrice,
                item.breadcrumb,
                item.stock,
                ",".join(item.image),
            ]
            self.writer.writerow(row)

        logging.info("Export completed")


if __name__ == "__main__":
    with open(FILE_NAME, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        Export(writer).start()
