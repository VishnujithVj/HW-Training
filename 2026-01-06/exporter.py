import csv
import logging
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# ======================
# CONFIG
# ======================
INPUT_CSV_FILE = "Eurospin_2026105.CSV"
OUTPUT_CSV_FILE = "eurospin_2026_01_07.csv"
DELIMITER = "|"

# ======================
# HELPERS
# ======================
def clean_html_text(value):
    if not value:
        return ""
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize(value):
    return (value or "").strip().lower()


def format_extraction_date(value):
    """Convert DD-MM-YYYY → YYYY-MM-DD"""
    try:
        return datetime.strptime(value.strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
    except Exception:
        return value or ""


def fix_competitor_name(value):
    """eurospine → eurospin"""
    if not value:
        return ""
    return value.replace("eurospine", "eurospin")


def fix_pdp_url(value):
    """Fix eurospine domain typo"""
    if not value:
        return ""
    return value.replace("eurospine.it", "eurospin.it")


def fix_image_url(value):
    """
    Fix eurospine domain typo in image URLs
    Example:
    https://laspesaonline.eurospine.it/... → https://laspesaonline.eurospin.it/...
    """
    if not value:
        return ""
    return value.replace("eurospine.it", "eurospin.it")


# ======================
# EXPORTER
# ======================
class Export:
    """Post-Processing CSV Exporter (Strict schema, no extra pipes)"""

    def __init__(self, writer):
        self.writer = writer
        self.seen_keys = set()

    def start(self):

        FILE_HEADERS = [
            "unique_id","competitor_name","store_name","store_addressline1",
            "store_addressline2","store_suburb","store_state","store_postcode",
            "store_addressid","extraction_date","product_name","brand",
            "brand_type","grammage_quantity","grammage_unit","drained_weight",
            "producthierarchy_level1","producthierarchy_level2",
            "producthierarchy_level3","producthierarchy_level4",
            "producthierarchy_level5","producthierarchy_level6",
            "producthierarchy_level7","regular_price","selling_price",
            "price_was","promotion_price","promotion_valid_from",
            "promotion_valid_upto","promotion_type","percentage_discount",
            "promotion_description","package_sizeof_sellingprice",
            "per_unit_sizedescription","price_valid_from","price_per_unit",
            "multi_buy_item_count","multi_buy_items_price_total","currency",
            "breadcrumb","pdp_url","variants","product_description",
            "instruction","storage_instructions","preparationinstructions",
            "instructionforuse","country_of_origin","allergens",
            "age_of_the_product","age_recommendations","flavour",
            "nutritions","nutritional_information","vitamins","labelling",
            "grade","region","packaging","receipies","processed_food",
            "barcode","frozen","chilled","organictype","cooking_part",
            "handmade","max_heating_temperature","special_information",
            "label_information","dimensions","special_nutrition_purpose",
            "feeding_recommendation","warranty","color","model_number",
            "material","usp","dosage_recommendation","tasting_note",
            "food_preservation","size","rating","review","file_name_1",
            "image_url_1","file_name_2","image_url_2","file_name_3",
            "image_url_3","competitor_product_key","fit_guide","occasion",
            "material_composition","style","care_instructions",
            "heel_type","heel_height","upc","features",
            "dietary_lifestyle","manufacturer_address","importer_address",
            "distributor_address","vinification_details",
            "recycling_information","return_address","alchol_by_volume",
            "beer_deg","netcontent","netweight","site_shown_uom",
            "ingredients","random_weight_flag","instock","promo_limit",
            "product_unique_key","multibuy_items_pricesingle","perfect_match",
            "servings_per_pack","warning","suitable_for",
            "standard_drinks","environmental","grape_variety","retail_limit"
        ]

        # Write headers
        self.writer.writerow(FILE_HEADERS)
        logging.info("CSV headers written")

        with open(INPUT_CSV_FILE, "r", encoding="utf-8", newline="") as infile:
            reader = csv.DictReader(
                infile,
                delimiter=DELIMITER,
                restkey="_extra_columns"
            )

            for item in reader:
                item.pop("_extra_columns", None)

                # ---------- DEDUP ----------
                dedup_key = (
                    normalize(item.get("unique_id")),
                    normalize(item.get("store_addressline")),
                    normalize(item.get("store_postcode")),
                )

                if dedup_key in self.seen_keys:
                    continue

                self.seen_keys.add(dedup_key)
                # --------------------------

                # Fix fields
                item["competitor_name"] = fix_competitor_name(item.get("competitor_name"))
                item["store_addressline1"] = item.get("store_addressline", "")
                item["extraction_date"] = format_extraction_date(item.get("extraction_date", ""))
                item["pdp_url"] = fix_pdp_url(item.get("pdp_url"))
                item["product_description"] = clean_html_text(item.get("product_description"))

                # 🔥 FIX IMAGE URLS
                item["image_url_1"] = fix_image_url(item.get("image_url_1"))
                item["image_url_2"] = fix_image_url(item.get("image_url_2"))
                item["image_url_3"] = fix_image_url(item.get("image_url_3"))

                # Product unique key
                uid = (item.get("unique_id") or "").strip()
                item["product_unique_key"] = f"{uid}P" if uid else ""

                # Exact column count (NO extra |)
                row = [item.get(h, "") for h in FILE_HEADERS]
                self.writer.writerow(row)

        logging.info(f"Export completed successfully. Unique rows: {len(self.seen_keys)}")


# ======================
# RUN
# ======================
if __name__ == "__main__":
    with open(OUTPUT_CSV_FILE, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(
            file,
            delimiter=DELIMITER,
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        Export(writer).start()
