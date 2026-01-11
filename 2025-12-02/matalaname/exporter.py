import csv
import logging
import re
import html
import json
from mongoengine import connect
from settings import MONGO_DB, FILE_NAME, FILE_HEADERS
from items import ProductDetailItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def dict_to_string(d):
    """Convert dict to: key: value, key: value"""
    if not d:
        return ""
    return ", ".join(f"{k}: {v}" for k, v in d.items())


class Export:
    """Export Matalan product details to CSV"""

    def __init__(self, writer):
        connect(db=MONGO_DB, alias="default", host="localhost", port=27017)
        self.writer = writer

    def fix_encoding(self, text):
        """Fix mojibake like â€™ â€œ â€¢ etc."""
        if not text:
            return ""

        replacements = {
            "â€™": "’",
            "â€œ": "“",
            "â€": "”",
            "â€“": "–",
            "â€”": "—",
            "â€˜": "‘",
            "â€¢": "•",
            "â€¦": "…",
            "â€": "”",
            "Â": "",
            "â€‌": "”",
            "â€Œ": "",
            "â€‹": "",
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)

        return text

    def clean_html(self, text):
        if not text:
            return ""
        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()

    def clean_value(self, val):
        if not val:
            return ""
        val = str(val)
        val = self.fix_encoding(val)
        val = self.clean_html(val)
        return val.strip().replace("\\", "")   

    def clean_dict(self, data):
        """Remove barcode + convert dict to 'key: value, key: value' string."""
        if not data:
            return ""

        blacklist = {"Barcode", "barcode", "bar_code", "bar code"}
        data = {k: v for k, v in data.items() if k not in blacklist}

        # convert dict → string using your format
        formatted = dict_to_string(data)
        formatted = self.clean_html(formatted)
        return formatted

    def handle_price(self, selling, regular):
        """If selling == regular, selling must be empty."""
        if not selling:
            return "", regular

        try:
            sp = float(selling)
            rp = float(regular) if regular else None

            if rp is not None and sp == rp:
                return "", rp
            else:
                return sp, rp

        except:
            return selling, regular

    def start(self):
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV headers written: {FILE_HEADERS}")

        for item in ProductDetailItem.objects()[:200]:

            # clean dict (converted to text)
            clean_details = self.clean_dict(item.product_details)

            # price logic
            selling, regular = self.handle_price(item.selling_price, item.regular_price)

            row = [
                self.clean_value(str(item.unique_id)),
                self.clean_value(item.url),
                self.clean_value(item.product_name),
                clean_details,
                self.clean_value(item.color),
                "",
                self.clean_value(item.size),
                self.clean_value(str(selling)),
                self.clean_value(str(regular)),
                self.clean_value(item.image),
                self.clean_value(item.description),
                self.clean_value(item.currency),
                self.clean_value(item.gender),
                "",
                self.clean_value(item.extraction_date),
            ]

            self.writer.writerow(row)

        logging.info("Data export completed successfully!")

    def close(self):
        logging.info("Export finished.")


if __name__ == "__main__":
    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(
            file,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            escapechar="\\"
        )
        exporter = Export(writer_file)
        exporter.start()
        exporter.close()
