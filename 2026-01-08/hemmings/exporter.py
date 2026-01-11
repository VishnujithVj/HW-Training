import csv
import logging
import re

# ======================
# CONFIG
# ======================
INPUT_CSV_FILE = "hemmings_sample.csv"
OUTPUT_CSV_FILE = "hemmings_2026_01_09_sample.csv"

EXPORT_LIMIT = None  # set int if needed

# ======================
# STRICT OUTPUT FIELD ORDER
# ======================
OUTPUT_FIELDS = [
    "make",
    "model",
    "year",
    "vin",
    "price",
    "mileage",
    "transmission",
    "engine",
    "color",
    "fuel_type",
    "body_style",
    "description",
    "image_urls",
    "source_link",
]

# ======================
# CSV → OUTPUT FIELD MAP
# ======================
CSV_FIELD_MAP = {
    "make": "make",
    "model": "model",
    "year": "year",
    "vin": "vin",
    "price": "price",
    "mileage": "mileage",
    "transmission": "transmission",
    "engine": "engine",
    "color": "color",
    "body style": "body_style",
    "description": "description",
    "source link": "source_link",
    "fuel type": "fuel_type",
    "image URLs": "image_urls",
}


class Export:
    """CSV → Cleaned CSV Exporter"""

    def clean_description(self, value: str) -> str:
        """
        Clean description:
        - fix bad UTF-8 chars
        - remove 'Description' prefix
        - remove newlines
        - normalize spaces
        """
        if not isinstance(value, str):
            return ""

        # Fix common mojibake characters
        replacements = {
            "â": "'",
            "â": "'",
            "â": '"',
            "â": '"',
            "â": "-",
            "â": "-",
        }
        for bad, good in replacements.items():
            value = value.replace(bad, good)

        # Remove "Description" prefix (only at start)
        value = re.sub(
            r"^\s*description\s*[:,\-]*\s*",
            "",
            value,
            flags=re.I
        )

        # Remove newlines & NBSP
        value = value.replace("\n", " ").replace("\r", " ").replace("\xa0", " ")

        # Normalize spaces
        value = re.sub(r"\s+", " ", value)

        return value.strip()

    def clean_value(self, value) -> str:
        return value.strip() if isinstance(value, str) else ""

    def clean_price(self, value) -> str:
        """
        "$89,500 " → "89500"
        """
        if not isinstance(value, str):
            return ""
        value = value.replace("$", "").replace(",", "")
        return re.sub(r"[^\d]", "", value)

    def start(self):
        logging.info("Starting CSV → CSV export")

        with open(INPUT_CSV_FILE, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)

        if EXPORT_LIMIT:
            rows = rows[:EXPORT_LIMIT]

        with open(OUTPUT_CSV_FILE, "w", encoding="utf-8", newline="") as out_file:
            writer = csv.DictWriter(out_file, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()

            for row in rows:
                record = {}

                for field in OUTPUT_FIELDS:
                    csv_key = next(
                        (k for k, v in CSV_FIELD_MAP.items() if v == field),
                        None
                    )

                    raw_value = row.get(csv_key, "") if csv_key else ""

                    if field == "price":
                        record[field] = self.clean_price(raw_value)

                    elif field == "description":
                        record[field] = self.clean_description(raw_value)

                    else:
                        record[field] = self.clean_value(raw_value)

                writer.writerow(record)

        logging.info(
            f"Export completed → {OUTPUT_CSV_FILE} "
            f"(total exported: {len(rows)})"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Export().start()
