#!/usr/bin/env python3
import asyncio
import logging
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from pymongo import MongoClient

REQUEST_TIMEOUT = 60000
MAX_CONCURRENT_PAGES = 5


class BillaParser:
    def __init__(self, mongo_uri="mongodb://localhost:27017", db_name="billa_site_db"):
        # MongoDB setup
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.urls_col = self.db["product_urls"]
        self.details_col = self.db["product_details"]

        # JSON file path
        self.json_file = Path("product_details.json")

        # Logging setup
        logging.basicConfig(
            filename="parser.log",
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )
        self.logger = logging.getLogger("BillaParser")

        # Semaphore for concurrency
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)

    async def run(self):
        self.logger.info("Starting Billa parser...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (compatible; BillaParser/1.0)"
            )

            urls_cursor = self.urls_col.find({}, {"product_urls": 1})
            total_urls = self.urls_col.count_documents({})
            self.logger.info(f"Found {total_urls} documents to parse")

            tasks = []
            for doc in urls_cursor:
                for url in doc.get("product_urls", []):
                    tasks.append(self.parse_product(context, url))

            await asyncio.gather(*[self.limited(task) for task in tasks])
            await browser.close()
        self.logger.info("Parser finished successfully.")

    async def limited(self, coro):
        async with self.semaphore:
            return await coro

    async def parse_product(self, context, url):
        page = await context.new_page()
        try:
            await page.goto(url, timeout=REQUEST_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=REQUEST_TIMEOUT)
        except Exception as e:
            self.logger.error(f"Failed to load {url}: {e}")
            await page.close()
            return

        # ---- Extract base product info ----
        sku_text = await self.extract_text(
            page, "//div[contains(@class,'ws-product-detail-main__sku')]"
        )
        unique_id = self.generate_unique_id(url)   # MD5 hash from URL
        product_name = await self.extract_text(page, "//h1")
        brand = await self.extract_text(page, "//a[@data-test='product-information-brand']")
        brand_type = self.extract_brand_type(brand)
        breadcrumb, hierarchy = await self.extract_breadcrumbs(page)
        grammage_q, grammage_unit = await self.extract_grammage(page)
        prices = await self.extract_prices(page)
        images = await self.extract_images(page, unique_id)
        ingredients, allergens = await self.extract_ingredients_allergens(page)
        nutrition_info = await self.extract_nutrition(page)
        further_info = await self.extract_further_information(page)

        # ---- SKU parsing for competitor_product_key & product_unique_key ----
        competitor_product_key, product_unique_key = None, None
        if sku_text:
            # Example: "Art. Nr.: 00-768102" → 768102P
            digits = re.findall(r"\d+", sku_text)
            if digits:
                competitor_product_key = sku_text.strip()
                product_unique_key = f"{digits[-1]}P"

        # ---------------- Schema ----------------
        data = {
            "unique_id": unique_id,
            "competitor_name": "Billa",
            "store_name": None,
            "store_addressline1": None,
            "store_addressline2": None,
            "store_suburb": None,
            "store_state": None,
            "store_postcode": None,
            "store_addressid": None,
            "extraction_date": datetime.utcnow(),

            "product_name": product_name,
            "brand": brand,
            "brand_type": brand_type,
            "grammage_quantity": grammage_q,
            "grammage_unit": grammage_unit,
            "drained_weight": None,
            **hierarchy,

            # Prices
            "regular_price": prices.get("regular_price"),
            "selling_price": prices.get("selling_price"),
            "price_was": prices.get("price_was"),
            "promotion_price": None,
            "promotion_valid_from": None,
            "promotion_valid_upto": None,
            "promotion_type": None,
            "percentage_discount": None,
            "promotion_description": None,
            "package_sizeof_sellingprice": None,
            "per_unit_sizedescription": None,
            "price_valid_from": None,
            "price_per_unit": prices.get("price_per_unit"),
            "multi_buy_item_count": prices.get("multi_buy_item_count"),
            "multi_buy_items_price_total": None,
            "currency": "EUR",

            # Metadata
            "breadcrumb": breadcrumb,
            "pdp_url": url,
            "variants": None,
            "product_description": await self.extract_text(
                page, "//div[contains(@class,'ws-product-slug-main__description-short')]"
            ),
            "instructions": None,
            "storage_instructions": None,
            "preparationinstructions": None,
            "instructionforuse": None,
            "country_of_origin": await self.extract_text(
                page,
                "//div[contains(text(),'Produktionsland')]/following-sibling::div"
            ),
            "allergens": allergens,
            "age_of_the_product": None,
            "age_recommendations": None,
            "flavour": None,
            "nutritions": None,
            "nutritional_information": nutrition_info,
            "vitamins": None,
            "labelling": None,
            "grade": None,
            "region": None,
            "packaging": None,
            "receipies": None,
            "processed_food": None,
            "barcode": None,
            "frozen": None,
            "chilled": None,
            "organictype": None,
            "cooking_part": None,
            "Handmade": None,
            "max_heating_temperature": None,
            "special_information": None,
            "label_information": further_info,
            "dimensions": None,
            "special_nutrition_purpose": None,
            "feeding_recommendation": None,
            "warranty": None,
            "color": None,
            "model_number": None,
            "material": None,
            "usp": None,
            "dosage_recommendation": None,
            "tasting_note": None,
            "food_preservation": None,
            "size": None,
            "rating": None,
            "review": None,

            # Images
            "file_name_1": images.get("file_name_1"),
            "image_url_1": images.get("image_url_1"),
            "file_name_2": images.get("file_name_2"),
            "image_url_2": images.get("image_url_2"),
            "file_name_3": images.get("file_name_3"),
            "image_url_3": images.get("image_url_3"),

            "competitor_product_key": competitor_product_key,
            "fit_guide": None,
            "occasion": None,
            "material_composition": None,
            "style": None,
            "care_instructions": None,
            "heel_type": None,
            "heel_height": None,
            "upc": None,
            "features": None,
            "dietary_lifestyle": None,
            "manufacturer_address": None,
            "importer_address": None,
            "distributor_address": None,
            "vinification_details": None,
            "recycling_information": None,
            "return_address": None,
            "alchol_by_volume": None,
            "beer_deg": None,
            "netcontent": None,
            "netweight": None,
            "site_shown_uom": product_name,
            "ingredients": ingredients,
            "random_weight_flag": None,
            "instock": None,
            "promo_limit": None,
            "product_unique_key": product_unique_key,
            "multibuy_items_pricesingle": None,
            "perfect_match": None,
            "servings_per_pack": None,
            "Warning": None,
            "suitable_for": None,
            "standard_drinks": None,
            "grape_variety": None,
            "retail_limit": None,
        }

        # Save to DB
        self.details_col.update_one({"pdp_url": url}, {"$set": data}, upsert=True)

        # Save to JSON
        with self.json_file.open("a", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
            f.write("\n")

        self.logger.info(f"Saved product: {product_name} ({url})")
        await page.close()

    # ---------------- Helpers ----------------
    def generate_unique_id(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def extract_brand_type(self, brand: str) -> str:
        """Classify brand type"""
        if not brand:
            return None
        private_labels = ["billa", "clever", "ja! natürlich", "ja!natürlich"]
        return "Private Label" if any(pl in brand.lower() for pl in private_labels) else "Manufacturer Brand"

    async def extract_text(self, page, xpath):
        try:
            element = await page.query_selector(f"xpath={xpath}")
            if element:
                return (await element.inner_text()).strip()
        except Exception:
            return None
        return None

    async def extract_breadcrumbs(self, page):
        breadcrumb_text = await self.extract_text(
            page, "//div[contains(@class,'ws-product-category-breadcrumbs')]"
        )
        if not breadcrumb_text:
            return None, {f"producthierarchy_level{i}": None for i in range(1, 8)}
        for sep in ["chevron_left", ">>", ">", "»"]:
            if sep in breadcrumb_text:
                levels = [lvl.strip() for lvl in breadcrumb_text.split(sep) if lvl.strip()]
                break
        else:
            levels = [breadcrumb_text.strip()]
        breadcrumb_str = " > ".join(levels)
        hierarchy = {
            f"producthierarchy_level{i}": levels[i - 1] if i <= len(levels) else None
            for i in range(1, 8)
        }
        return breadcrumb_str, hierarchy

    async def extract_grammage(self, page):
        text = await self.extract_text(
            page, "//ul[@data-test='product-information-piece-description']/li[1]"
        )
        if not text:
            return None, None
        match = re.match(r"([\d.,]+)\s*([a-zA-Z]+)", text)
        if match:
            return match.group(1), match.group(2)
        return text, None

    async def extract_prices(self, page):
        data = {}
        data["regular_price"] = await self.extract_text(
            page, "//div[@data-test='product-price-type']//div[contains(@class,'__value')]"
        )
        data["selling_price"] = await self.extract_text(
            page, "//div[contains(@class,'ws-product-price-strike')]"
        )
        data["price_was"] = await self.extract_text(
            page, "//div[contains(@class,'ws-product-price-strike')]"
        )
        data["price_per_unit"] = await self.extract_text(
            page, "//div[@class='ws-product-price-type__label']"
        )
        data["multi_buy_item_count"] = await self.extract_text(
            page, "//div[contains(@class,'ws-product-price__additional-info')]"
        )
        return data

    async def extract_images(self, page, unique_id):
        # Corrected selector: actual image tag has this class
        imgs = await page.query_selector_all(
            "//img[contains(@class,'ws-product-detail-image-inner-image__image') or @data-test='product-detail-image']"
        )
        out = {}
        for i, el in enumerate(imgs[:3], 1):
            src = await el.get_attribute("src")
            if src:
                out[f"file_name_{i}"] = f"{unique_id}_{i}.jpg"
                out[f"image_url_{i}"] = src
        return out

    async def extract_ingredients_allergens(self, page):
        ingredients = await self.extract_text(
            page,
            "//div[contains(text(),'Zutaten') or contains(text(),'Ingredients')]/following-sibling::div",
        )
        allergens = await self.extract_text(
            page, "//div[contains(text(),'Allergene')]/following-sibling::div"
        )
        return ingredients, allergens

    async def extract_nutrition(self, page):
        rows = await page.query_selector_all(
            "//div[contains(@class,'ws-product-detail-nutrition')]//tr"
        )
        nutrition = {}
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) >= 3:
                name = (await cols[0].inner_text()).strip()
                per100g = (await cols[1].inner_text()).strip()
                perserve = (await cols[2].inner_text()).strip()
                nutrition[name] = {"per_100g": per100g, "per_serving": perserve}
        return nutrition if nutrition else None

    async def extract_further_information(self, page):
        return await self.extract_text(
            page, "//div[contains(@class,'ws-product-detail-row__content')]"
        )


if __name__ == "__main__":
    parser = BillaParser()
    asyncio.run(parser.run())
