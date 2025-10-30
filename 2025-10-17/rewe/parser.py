import logging
import re
import json
from datetime import datetime, timezone
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from settings import HEADERS, MONGO_DB
from items import ProductItem, ProductUrlItem, ProductFailedItem


class Parser:
    """REWE Parser — Company Standard Template"""

    def __init__(self):
        """Initialize Mongo connection"""
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")


    # START
    def start(self):
        """Start parsing process"""
        logging.info("🚀 Starting REWE parser")

        urls = ProductUrlItem.objects.only("url", "category_url", "subcategory_url")
        if not urls:
            logging.warning("No product URLs found in MongoDB")
            return

        for record in urls:
            url = record.url
            try:
                response = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=30)
                if response.status_code == 200:
                    self.parse_item(url, response, record)
                else:
                    logging.error(f"HTTP {response.status_code} for {url}")
                    self.failed(url)
            except Exception as e:
                logging.error(f"Fetch error for {url}: {e}")
                self.failed(url)

    # CLOSE
    def close(self):
        """Close connections"""
        logging.info("Parser completed successfully")
        self.mongo.close()


    # PARSE ITEM
    def parse_item(self, url, response, meta):
        """Parse product page"""

        sel = Selector(text=response.text)
        script = sel.xpath('//script[contains(@id,"pdpr-propstore")]/text()').get()
        data = json.loads(script).get("productData", {}) if script else {}
        html_fields = self.extract_html_fields(sel)


        # EXTRACTION SCRIPT
        item = {}
        item["pdp_url"] = url
        item["unique_id"] = str(data.get("productId", "")).strip()
        item["product_unique_key"] = item["unique_id"]
        item["competitor_name"] = "REWE"
        item["store_name"] = "REWE Online"
        item["currency"] = "EUR"
        item["instock"] = True
        item["extraction_date"] = datetime.now(timezone.utc)

        # --- Pricing ---
        pricing = data.get("pricing", {})
        item["product_name"] = data.get("productName", "").strip()
        item["brand"] = data.get("brandKey", "").strip()
        item["barcode"] = str(data.get("gtin", "")).strip()
        item["regular_price"] = self.price_to_str(pricing.get("regularPrice"))
        item["selling_price"] = self.price_to_str(pricing.get("price"))
        item["promotion_price"] = self.price_to_str(pricing.get("discount", {}).get("rate"))
        item["promotion_valid_upto"] = str(pricing.get("discount", {}).get("validTo", ""))

        # --- Store Info ---
        merchant = data.get("merchant", {}).get("address", {})
        item["store_addressline1"] = merchant.get("street", "")
        item["store_addressline2"] = merchant.get("houseNumber", "")
        item["store_suburb"] = merchant.get("city", "")
        item["store_postcode"] = merchant.get("zipCode", "")
        item["store_state"] = merchant.get("country", "")
        item["store_addressid"] = str(data.get("marketCode", ""))

        # --- Grammage ---
        grammage_text = pricing.get("grammage", html_fields.get("grammage", ""))
        qty, unit = self.extract_grammage(grammage_text)
        item["grammage_quantity"] = qty
        item["grammage_unit"] = unit
        item["price_per_unit"] = self.extract_price_unit(grammage_text)

        # --- Manufacturer ---
        manufacturer = data.get("manufacturer", {})
        phone = ""
        for c in manufacturer.get("communicationChannels", []):
            if c.get("name") == "communicationChannelTelephone":
                phone = c.get("value", "")

        item["manufacturer_name"] = manufacturer.get("name", "") or html_fields.get("manufacturer_name", "")
        item["manufacturer_address"] = manufacturer.get("communicationAddress", "") or html_fields.get("manufacturer_address", "")
        item["manufacturer_phone"] = phone or html_fields.get("manufacturer_phone", "")

        # --- Description ---
        desc = data.get("tradeItemMarketingMessage", "") or html_fields.get("description", "")
        item["product_description"] = re.sub(r"\s+", " ", desc).strip()

        # --- Ingredients & Allergens ---
        item["ingredients"] = data.get("ingredientStatement", "") or html_fields.get("ingredients", "")
        allergens = html_fields.get("allergens", "")
        allergens = re.sub(r"^(Allergenhinweise|Allergens)\s*[::]?\s*", "", allergens, flags=re.I).strip()
        item["allergens"] = allergens

        # --- Storage & Instructions ---
        storage = html_fields.get("storage_instructions", "")
        storage = re.sub(r"^(Aufbewahrungshinweise|Storage instructions)\s*[::]?\s*", "", storage, flags=re.I).strip()
        item["storage_instructions"] = storage

        instr = html_fields.get("instruction_for_use", "")
        instr = re.sub(r"^(Verwendungshinweise|Usage instructions)\s*[::]?\s*", "", instr, flags=re.I).strip()
        item["instruction_for_use"] = instr
        item["preparation_instructions"] = html_fields.get("preparation_instructions", "")

        # --- Warning ---
        warning_data = data.get("hazardsAndWarnings", {})
        if warning_data:
            risk = warning_data.get("riskPhraseCode", "")
            safety = warning_data.get("safetyPhraseCode", "")
            warning_text = " ".join([risk.strip(), safety.strip()]).strip()
        else:
            warning_text = html_fields.get("warning", "")
        item["warning"] = warning_text

        # --- Breadcrumbs ---
        crumbs = self.extract_breadcrumbs(sel)
        for i, name in enumerate(crumbs):
            item[f"producthierarchy_level{i + 1}"] = name
        item["breadcrumb"] = " > ".join(crumbs)


        # CLEAN & SAVE
        item = self.clean_data(item)
        try:
            ProductItem(**item).save()
            logging.info(f"Saved: {item['product_name']} ({item['unique_id']})")
        except Exception as e:
            logging.warning(f"Failed to save product {url}: {e}")

    
    # EXTRACTION HTML
    def extract_html_fields(self, sel):
        """Extract raw HTML fields"""
        fields = {}
        fields["grammage"] = sel.xpath('//div[contains(@class,"pdsr-Grammage")]/text()').get(default="").strip()

        desc_parts = sel.xpath('//div[contains(@class,"pdpr-ProductDescription__Content")]//text()').getall()
        fields["description"] = " ".join([d.strip() for d in desc_parts if d.strip()])

        fields["ingredients"] = " ".join(sel.xpath('//div[h3[contains(.,"Zutaten")]]//text()').getall()).strip()
        fields["allergens"] = " ".join(sel.xpath('//div[h3[contains(.,"Allergene")]]//text()').getall()).strip()
        fields["storage_instructions"] = " ".join(sel.xpath(
            '//div[h3[contains(.,"Aufbewahrungshinweise") or contains(.,"Storage")]]//text()'
        ).getall()).strip()
        fields["instruction_for_use"] = " ".join(sel.xpath(
            '//div[h3[contains(.,"Verwendungshinweise")]]//text()'
        ).getall()).strip()
        fields["preparation_instructions"] = " ".join(sel.xpath(
            '//div[h3[contains(.,"Zubereitungsanweisungen")]]//text()'
        ).getall()).strip()
        fields["manufacturer_name"] = sel.xpath('//div[h3[contains(.,"Kontaktname")]]//text()').get(default="").strip()
        fields["manufacturer_address"] = sel.xpath('//div[h3[contains(.,"Kontaktadresse")]]//text()').get(default="").strip()
        fields["manufacturer_phone"] = sel.xpath('//div[h3[contains(.,"Tel")]]//text()').get(default="").strip()
        warn = sel.xpath('//div[contains(@class,"pdpr-Attribute") and contains(.,"Warnhinweise")]//text()').getall()
        fields["warning"] = " ".join([w.strip() for w in warn if w.strip()])

        return fields

    def extract_breadcrumbs(self, sel):
        crumbs = sel.xpath(
            '//nav[contains(@aria-label,"Seitenpfad") or contains(@aria-label,"Breadcrumb")]//a/text() | '
            '//nav[contains(@aria-label,"Seitenpfad") or contains(@aria-label,"Breadcrumb")]//span/text()'
        ).getall()
        return [c.strip() for c in crumbs if c.strip()]

    def extract_price_unit(self, text):
        m = re.search(r"\(([^)]+)\)", text or "")
        return m.group(1) if m else ""

    def extract_grammage(self, text):
        if not text:
            return "", ""
        text = re.sub(r"\(.*?\)", "", text).strip()
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)", text)
        return (m.group(1).replace(",", "."), m.group(2)) if m else ("", "")

    def price_to_str(self, val):
        if not val:
            return ""
        try:
            return f"{float(val) / 100:.2f}" if isinstance(val, int) else str(val)
        except Exception:
            return str(val)
    # clean
    def clean_data(self, item):
        return {k: (re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else (v or "")) for k, v in item.items()}

    def failed(self, url):
        ProductFailedItem(url=url).save()
        logging.warning(f"Failed URL saved: {url}")


# MAIN
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()
