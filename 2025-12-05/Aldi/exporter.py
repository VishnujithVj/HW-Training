import csv
import logging
from pymongo import MongoClient
from settings import (
    MONGO_DB,
    MONGO_URI,
    MONGO_COLLECTION_DATA,
    FILE_NAME,
    FILE_HEADERS
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# -----------------------------
# UTF-8 MOJIBAKE FIXER
# -----------------------------
def fix_mojibake(text):
    """Fix common UTF-8 encoding issues"""
    if not isinstance(text, str):
        return text

    replacements = {
        "â¦": "…",
        "â€™": "'",
        "â€œ": "\"",
        "â€": "\"",
        "â€¢": "•",
        "â€“": "–",
        "â€”": "—",
        "â„¢": "™",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    try:
        text = text.encode("latin1").decode("utf8")
    except:
        pass

    return text


class Export:
    """Post-Processing - Export Aldi product data to CSV"""

    FORCE_STRING_FIELDS = {
        "unique_id",
        "competitor_product_key",
        "product_unique_key",
    }

    def __init__(self, writer):
        self.client = MongoClient(MONGO_URI)
        self.mongo = self.client[MONGO_DB]
        self.writer = writer
        logging.info("MongoDB connected for export")

    def clean_value(self, value, header=None):
        """Clean and format field values"""
        
        # Force packaging to empty
        if header == "packaging":
            return ""

        # Always treat these fields as strings
        if header in self.FORCE_STRING_FIELDS:
            return "" if value is None else str(value)

        if value is None:
            return ""

        value = str(value).strip()

        # -------------------------
        # NEW — Clean N/A variations
        # -------------------------
        na_val = (
            value.lower()
            .replace(".", "")
            .replace("/", "")
            .replace("-", "")
            .strip()
        )
        if na_val in {"n", "na", "n a"}:
            return ""

        # Fix UTF-8 mojibake
        value = fix_mojibake(value)

        # Convert list to semicolon-separated string
        if isinstance(value, list):
            return "; ".join([fix_mojibake(str(x)) for x in value])

        # Convert dict to key:value pairs
        if isinstance(value, dict):
            return "; ".join([f"{k}:{fix_mojibake(str(v))}" for k, v in value.items()])

        # grammage_unit lowercase
        if header == "grammage_unit" and value:
            return value.lower()

        return value


    def start(self):
        """Export as CSV file"""
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"Headers written: {len(FILE_HEADERS)} columns")

        count = 0

        for item in self.mongo[MONGO_COLLECTION_DATA].find({}, no_cursor_timeout=True):

            # Extract & clean each field
            unique_id = self.clean_value(item.get("unique_id"), "unique_id")
            competitor_name = self.clean_value(item.get("competitor_name"))
            store_name = self.clean_value(item.get("store_name"))
            store_addressline1 = self.clean_value(item.get("store_addressline1"))
            store_addressline2 = self.clean_value(item.get("store_addressline2"))
            store_suburb = self.clean_value(item.get("store_suburb"))
            store_state = self.clean_value(item.get("store_state"))
            store_postcode = self.clean_value(item.get("store_postcode"))
            store_addressid = self.clean_value(item.get("store_addressid"))
            extraction_date = self.clean_value(item.get("extraction_date"))
            product_name = self.clean_value(item.get("product_name"))
            brand = self.clean_value(item.get("brand"))
            brand_type = self.clean_value(item.get("brand_type"))
            grammage_quantity = self.clean_value(item.get("grammage_quantity"))
            grammage_unit = self.clean_value(item.get("grammage_unit"), "grammage_unit")
            drained_weight = self.clean_value(item.get("drained_weight"))
            producthierarchy_level1 = self.clean_value(item.get("producthierarchy_level1"))
            producthierarchy_level2 = self.clean_value(item.get("producthierarchy_level2"))
            producthierarchy_level3 = self.clean_value(item.get("producthierarchy_level3"))
            producthierarchy_level4 = self.clean_value(item.get("producthierarchy_level4"))
            producthierarchy_level5 = self.clean_value(item.get("producthierarchy_level5"))
            producthierarchy_level6 = self.clean_value(item.get("producthierarchy_level6"))
            producthierarchy_level7 = self.clean_value(item.get("producthierarchy_level7"))
            regular_price = self.clean_value(item.get("regular_price"))
            selling_price = self.clean_value(item.get("selling_price"))
            price_was = self.clean_value(item.get("price_was"))
            promotion_price = self.clean_value(item.get("promotion_price"))
            promotion_valid_from = self.clean_value(item.get("promotion_valid_from"))
            promotion_valid_upto = self.clean_value(item.get("promotion_valid_upto"))
            promotion_type = self.clean_value(item.get("promotion_type"))
            percentage_discount = self.clean_value(item.get("percentage_discount"))
            promotion_description = self.clean_value(item.get("promotion_description"))
            package_sizeof_sellingprice = self.clean_value(item.get("package_sizeof_sellingprice"))
            per_unit_sizedescription = self.clean_value(item.get("per_unit_sizedescription"))
            price_valid_from = self.clean_value(item.get("price_valid_from"))
            price_per_unit = self.clean_value(item.get("price_per_unit"))
            multi_buy_item_count = self.clean_value(item.get("multi_buy_item_count"))
            multi_buy_items_price_total = self.clean_value(item.get("multi_buy_items_price_total"))
            currency = self.clean_value(item.get("currency"))
            breadcrumb = self.clean_value(item.get("breadcrumb"))
            pdp_url = self.clean_value(item.get("pdp_url"))
            variants = self.clean_value(item.get("variants"))
            product_description = self.clean_value(item.get("product_description"))
            instructions = self.clean_value(item.get("instructions"))
            storage_instructions = self.clean_value(item.get("storage_instructions"))
            preparationinstructions = self.clean_value(item.get("preparationinstructions"))
            instructionforuse = self.clean_value(item.get("instructionforuse"))
            country_of_origin = self.clean_value(item.get("country_of_origin"))
            allergens = self.clean_value(item.get("allergens"))
            age_of_the_product = self.clean_value(item.get("age_of_the_product"))
            age_recommendations = self.clean_value(item.get("age_recommendations"))
            flavour = self.clean_value(item.get("flavour"))
            nutritions = self.clean_value(item.get("nutritions"))
            nutritional_information = self.clean_value(item.get("nutritional_information"))
            vitamins = self.clean_value(item.get("vitamins"))
            labelling = self.clean_value(item.get("labelling"))
            grade = self.clean_value(item.get("grade"))
            region = self.clean_value(item.get("region"))
            packaging = self.clean_value(item.get("packaging"), "packaging")
            receipies = self.clean_value(item.get("receipies"))
            processed_food = self.clean_value(item.get("processed_food"))
            barcode = self.clean_value(item.get("barcode"))
            frozen = self.clean_value(item.get("frozen"))
            chilled = self.clean_value(item.get("chilled"))
            organictype = self.clean_value(item.get("organictype"))
            cooking_part = self.clean_value(item.get("cooking_part"))
            Handmade = self.clean_value(item.get("Handmade"))
            max_heating_temperature = self.clean_value(item.get("max_heating_temperature"))
            special_information = self.clean_value(item.get("special_information"))
            label_information = self.clean_value(item.get("label_information"))
            dimensions = self.clean_value(item.get("dimensions"))
            special_nutrition_purpose = self.clean_value(item.get("special_nutrition_purpose"))
            feeding_recommendation = self.clean_value(item.get("feeding_recommendation"))
            warranty = self.clean_value(item.get("warranty"))
            color = self.clean_value(item.get("color"))
            model_number = self.clean_value(item.get("model_number"))
            material = self.clean_value(item.get("material"))
            usp = self.clean_value(item.get("usp"))
            dosage_recommendation = self.clean_value(item.get("dosage_recommendation"))
            tasting_note = self.clean_value(item.get("tasting_note"))
            food_preservation = self.clean_value(item.get("food_preservation"))
            size = self.clean_value(item.get("size"))
            rating = self.clean_value(item.get("rating"))
            review = self.clean_value(item.get("review"))
            file_name_1 = self.clean_value(item.get("file_name_1"))
            image_url_1 = self.clean_value(item.get("image_url_1"))
            file_name_2 = self.clean_value(item.get("file_name_2"))
            image_url_2 = self.clean_value(item.get("image_url_2"))
            file_name_3 = self.clean_value(item.get("file_name_3"))
            image_url_3 = self.clean_value(item.get("image_url_3"))
            competitor_product_key = self.clean_value(item.get("competitor_product_key"), "competitor_product_key")
            fit_guide = self.clean_value(item.get("fit_guide"))
            occasion = self.clean_value(item.get("occasion"))
            material_composition = self.clean_value(item.get("material_composition"))
            style = self.clean_value(item.get("style"))
            care_instructions = self.clean_value(item.get("care_instructions"))
            heel_type = self.clean_value(item.get("heel_type"))
            heel_height = self.clean_value(item.get("heel_height"))
            upc = self.clean_value(item.get("upc"))
            features = self.clean_value(item.get("features"))
            dietary_lifestyle = self.clean_value(item.get("dietary_lifestyle"))
            manufacturer_address = self.clean_value(item.get("manufacturer_address"))
            importer_address = self.clean_value(item.get("importer_address"))
            distributor_address = self.clean_value(item.get("distributor_address"))
            vinification_details = self.clean_value(item.get("vinification_details"))
            recycling_information = self.clean_value(item.get("recycling_information"))
            return_address = self.clean_value(item.get("return_address"))
            alchol_by_volume = self.clean_value(item.get("alchol_by_volume"))
            beer_deg = self.clean_value(item.get("beer_deg"))
            netcontent = self.clean_value(item.get("netcontent"))
            netweight = self.clean_value(item.get("netweight"))
            site_shown_uom = self.clean_value(item.get("site_shown_uom"))
            ingredients = self.clean_value(item.get("ingredients"))
            random_weight_flag = self.clean_value(item.get("random_weight_flag"))
            instock = self.clean_value(item.get("instock"))
            promo_limit = self.clean_value(item.get("promo_limit"))
            product_unique_key = self.clean_value(item.get("product_unique_key"), "product_unique_key")
            multibuy_items_pricesingle = self.clean_value(item.get("multibuy_items_pricesingle"))
            perfect_match = self.clean_value(item.get("perfect_match"))
            servings_per_pack = self.clean_value(item.get("servings_per_pack"))
            Warning = self.clean_value(item.get("Warning"))
            suitable_for = self.clean_value(item.get("suitable_for"))
            standard_drinks = self.clean_value(item.get("standard_drinks"))
            environmental = self.clean_value(item.get("environmental"))
            grape_variety = self.clean_value(item.get("grape_variety"))
            retail_limit = self.clean_value(item.get("retail_limit"))

            # Build data row in exact header order
            data = [
                unique_id, competitor_name, store_name, store_addressline1, store_addressline2,
                store_suburb, store_state, store_postcode, store_addressid, extraction_date,
                product_name, brand, brand_type, grammage_quantity, grammage_unit,
                drained_weight, producthierarchy_level1, producthierarchy_level2, producthierarchy_level3,
                producthierarchy_level4, producthierarchy_level5, producthierarchy_level6, producthierarchy_level7,
                regular_price, selling_price, price_was, promotion_price, promotion_valid_from,
                promotion_valid_upto, promotion_type, percentage_discount, promotion_description,
                package_sizeof_sellingprice, per_unit_sizedescription, price_valid_from, price_per_unit,
                multi_buy_item_count, multi_buy_items_price_total, currency, breadcrumb,
                pdp_url, variants, product_description, instructions, storage_instructions,
                preparationinstructions, instructionforuse, country_of_origin, allergens, age_of_the_product,
                age_recommendations, flavour, nutritions, nutritional_information, vitamins,
                labelling, grade, region, packaging, receipies, processed_food,
                barcode, frozen, chilled, organictype, cooking_part, Handmade,
                max_heating_temperature, special_information, label_information, dimensions, special_nutrition_purpose,
                feeding_recommendation, warranty, color, model_number, material, usp,
                dosage_recommendation, tasting_note, food_preservation, size, rating, review,
                file_name_1, image_url_1, file_name_2, image_url_2, file_name_3, image_url_3,
                competitor_product_key, fit_guide, occasion, material_composition, style, care_instructions,
                heel_type, heel_height, upc, features, dietary_lifestyle, manufacturer_address,
                importer_address, distributor_address, vinification_details, recycling_information, return_address,
                alchol_by_volume, beer_deg, netcontent, netweight, site_shown_uom, ingredients,
                random_weight_flag, instock, promo_limit, product_unique_key, multibuy_items_pricesingle,
                perfect_match, servings_per_pack, Warning, suitable_for, standard_drinks,
                environmental, grape_variety, retail_limit
            ]

            self.writer.writerow(data)
            count += 1

            if count % 50 == 0:
                logging.info(f"Exported {count} products...")

            # -------------------------
            # Limit to 200 ROWS
            # -------------------------
            if count >= 200:
                logging.info("Reached 200 rows — stopping export.")
                break

        logging.info(f"Export complete. Total exported: {count}")

    def close(self):
        self.client.close()
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(
            file,
            delimiter="|",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )

        export = Export(writer)
        export.start()
        export.close()

    logging.info(f"CSV file '{FILE_NAME}' created successfully")
