import logging
import re
import json
from datetime import datetime
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from settings import HEADERS, MONGO_DB
from items import ProductItem, ProductUrlItem, ProductFailedItem


class Parser:
    """REWE Parser """

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info(" MongoDB connected")

    def start(self):

        urls = ProductUrlItem.objects.only("url")
        if not urls:
            logging.warning(" No product URLs found")
            return

        for record in urls:
            url = record.url
            response = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=30)
            if response.status_code == 200:
                self.parse_item(url, response)
            else:
                logging.error(f" HTTP {response.status_code} for {url}")
                self.failed(url)


    def close(self):
        self.mongo.close()
        logging.info("Parser completed")

    def parse_item(self, url, response):
        """item part"""

        sel = Selector(text=response.text)

        """ XPATH """
        JSON_SCRIPT_XPATH = '//script[contains(@id,"pdpr-propstore")]/text()'
        STORE_ADDRESS_XPATH = '//span[contains(@class,"gbmc-header-link__text") and contains(@class,"gbmc-customer-zipcode-qa")]/text()'
        DESCRIPTION_XPATH = '//div[contains(@class,"pdpr-ProductDescription__Content")]//text()'
        ARTICLE_NUMBER_XPATH = '//div[contains(@class,"pdpr-ArticleNumber")]/text()'
        BREADCRUMBS_XPATH = '//nav[contains(@aria-label,"Breadcrumb") or contains(@aria-label,"Seitenpfad")]//a/text() | //nav[contains(@aria-label,"Breadcrumb") or contains(@aria-label,"Seitenpfad")]//span/text()'
        NUTRITION_TABLE_XPATH = '//table[contains(@class,"pdpr-NutritionTable")]//tr'
        COUNTRY_OF_ORIGIN_XPATH = '//div[contains(@class,"pdpr-Attribute")][.//h3[contains(., "Ursprung")]]'

        """ EXTRACT """
        json_data = self.extract_json_data(sel.xpath(JSON_SCRIPT_XPATH).get())
        store_address = sel.xpath(STORE_ADDRESS_XPATH).get()
        
        """ Product Description """
        description = " ".join(sel.xpath(DESCRIPTION_XPATH).getall()).strip() or (
            (lambda m: f"Artikelnummer {m.group()}" if m else "Product description not available")(
                re.search(r"\d+", (sel.xpath(ARTICLE_NUMBER_XPATH).get() or "").strip())
            )
        )

        """ Breadcrumbs """
        breadcrumbs = [x.strip() for x in sel.xpath(BREADCRUMBS_XPATH).getall() if x.strip()]
        
        """ Country of Origin """
        country_origin = (
            re.sub(r'^.*Ursprung\s*:\s*', '', (sel.xpath(COUNTRY_OF_ORIGIN_XPATH).xpath('string()').get() or ''), flags=re.IGNORECASE).strip()
            if sel.xpath(COUNTRY_OF_ORIGIN_XPATH).get()
            else ''
        )

        """ Nutrition table """
        nutrition = []
        for row in sel.xpath(NUTRITION_TABLE_XPATH):
            key = row.xpath('./td[1]//text()').get()
            val = row.xpath('./td[2]//text()').get()
            if key and val:
                nutrition.append(f"{key.strip()}: {val.strip()}")
        
        """ Ingredients & Allergens """
        ingredients = self.extract_section_text(sel, "Ingredients", "Zutaten")
        allergens = self.extract_section_text(sel, "Allergens", "Allergene")

        """ product_name/id """
        unique_id = str(json_data.get("productId", "")).strip()
        product_name = str(json_data.get("productName", "")).strip()
        
        """ Pricing """
        pricing = json_data.get("pricing", {})
        regular_price = self.format_price(pricing.get("regularPrice"))
        selling_price = self.format_price(pricing.get("price"))
        
        """ Discount """
        discount = pricing.get("discount", {})
        has_discount = discount.get("rate") and pricing.get("price") != pricing.get("regularPrice")
        
        """ Grammage """
        grammage_text = pricing.get("grammage", "")
        grammage_qty, grammage_unit = self.extract_grammage(grammage_text)
        price_per_unit_match = re.search(r"\(([^)]+)\)", grammage_text)
        price_per_unit = price_per_unit_match.group(1) if price_per_unit_match else ""
        
        """ Store address """
        if store_address and any(x in store_address.lower() for x in ["standort", "wählen"]):
            store_address = "Schanzenstraße 6-20, 51063 Cologne"

        """ ITEM """
        item = {}
        item["unique_id"] = unique_id
        item["product_unique_key"] = f"{unique_id}P"
        item["competitor_name"] = "REWE"
        item["store_name"] = "REWE Online"
        item["store_addressline1"] = store_address.strip() if store_address else "Schanzenstraße 6-20, 51063 Cologne"
        item["currency"] = "EUR"
        item["extraction_date"] = datetime.now().strftime("%Y-%m-%d")
        item["pdp_url"] = url
        item["product_name"] = product_name
        item["brand"] = str(json_data.get("brandKey", "")).strip()
        item["barcode"] = str(json_data.get("gtin", "")).strip()
        item["instock"] = bool(json_data.get("isBuyable", True))
        item["regular_price"] = regular_price
        item["selling_price"] = selling_price
        item["promotion_price"] = selling_price if has_discount else ""
        item["price_was"] = regular_price if has_discount else ""
        item["percentage_discount"] = f"{discount.get('rate')}%" if has_discount else ""
        item["promotion_valid_upto"] = str(discount.get("validTo", "")).strip() if has_discount else ""
        item["promotion_description"] = ""
        item["grammage_quantity"] = grammage_qty
        item["grammage_unit"] = grammage_unit
        item["price_per_unit"] = price_per_unit
        item["site_shown_uom"] = re.sub(r"\s*\(.*?\)", "", grammage_text).strip() if grammage_text else ""
        
        for i in range(1, 8):
            item[f"producthierarchy_level{i}"] = breadcrumbs[i - 1] if i <= len(breadcrumbs) else ""
        item["breadcrumb"] = " > ".join(breadcrumbs)
        
        item["product_description"] = json_data.get("tradeItemMarketingMessage", "") or description
        item["ingredients"] = json_data.get("ingredientStatement", "") or ingredients
        item["allergens"] = allergens
        item["nutritional_information"] = "; ".join(nutrition)
        item["country_of_origin"] = country_origin
        item["organictype"] = "Organic" if json_data.get("bio") else "Non-Organic"
        
        """ Images """
        images = []
        for media in json_data.get("mediaInformation", []):
            if media.get("type") == "image" and media.get("mediaUrl"):
                images.append(media["mediaUrl"])
        
        for i in range(1, 4):
            if i <= len(images):
                item[f"file_name_{i}"] = f"image_{i}.jpg"
                item[f"image_url_{i}"] = images[i - 1]
            else:
                item[f"file_name_{i}"] = ""
                item[f"image_url_{i}"] = ""
        
        item["competitor_product_key"] = unique_id
        item["manufacturer_address"] = json_data.get("manufacturer", {}).get("communicationAddress", "")
        
        cleaned_item = {}
        for k, v in item.items():
            if isinstance(v, str):
                cleaned_item[k] = re.sub(r"\s+", " ", v).strip()
            elif v is None:
                cleaned_item[k] = ""
            else:
                cleaned_item[k] = v
        
        """Save to MongoDB"""
        self.save_product(cleaned_item)
        logging.info(f" Saved: {product_name}")

    def extract_json_data(self, script):
        """Extract JSON data from script"""
        if not script:
            return {}
        try:
            full_data = json.loads(script)
            product_data = full_data.get("productData", {})
            product_data['_full_json'] = full_data
            return product_data
        except json.JSONDecodeError:
            return {}

    def extract_section_text(self, sel, english_key, german_key):
        """Extract section text by heading"""
        xpath = f'//div[h3[contains(.,"{english_key}") or contains(.,"{german_key}")]]//text()'
        texts = sel.xpath(xpath).getall()
        return " ".join([x.strip() for x in texts if x.strip()])

    def format_price(self, price):
        """Format price to string"""
        if not price:
            return ""
        if isinstance(price, (int, float)):
            return f"{float(price) / 100:.2f}"
        return str(price)

    def extract_grammage(self, text):
        """Extract grammage quantity and unit"""
        if not text:
            return "", ""
        text = re.sub(r"\(.*?\)", "", text).strip()
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*([a-zA-Zµ]+)", text)
        if match:
            return match.group(1).replace(",", "."), match.group(2)
        return "", ""

    def save_product(self, item):
        """Save product to MongoDB"""
        try:
            ProductItem(**item).save()
        except Exception as e:
            logging.error(f" Save error: {e}")

    def failed(self, url):
        """Record failed URL"""
        ProductFailedItem(url=url).save()
        logging.warning(f"Failed URL saved: {url}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = Parser()
    parser.start()
    parser.close()