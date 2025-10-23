import logging
import re
import json
from datetime import datetime, timezone
from parsel import Selector
import requests
from settings import HEADERS
from items import ProductItem, ProductUrlItem


class Parser:
    """BIPA Parser - Company Standard Template"""

    def __init__(self):
        """initialize connections"""
        self.mongo = ""

    # START    
    def start(self):
        """start code"""
        logging.info("Starting parser")

        urls = ProductUrlItem.objects().only("url")
        if not urls:
            logging.warning("No product URLs found in MongoDB")
            return

        for record in urls:
            url = record.url
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                self.parse_item(url, response)
            else:
                logging.error(f"Failed: {url} ({response.status_code})")

    
    # CLOSE
    def close(self):
        """connection close"""
        logging.info("Parser completed")
        self.mongo.close()

    # PARSE ITEM
    def parse_item(self, url, response):
        """item part"""

        sel = Selector(text=response.text)


        # XPATH SECTION
        JSON_LD_XPATH = '//script[@type="application/ld+json"]/text()'
        PRICE_XPATH = '//span[contains(@class, "price")]//text()'
        NAME_XPATH = '//h1//text()'
        BRAND_XPATH = '//meta[@property="product:brand"]/@content'
        DESC_XPATH = '//meta[@name="description"]/@content'
        BREADCRUMB_XPATH = '//nav[contains(@aria-label, "breadcrumb")]//a//text()'
        IMAGE_XPATH = '//img[contains(@class, "product")]/@src'

        # EXTRACT SECTION
        product_id = self.extract_product_id(url)
        product_name = sel.xpath(NAME_XPATH).get()
        brand = sel.xpath(BRAND_XPATH).get()
        description = sel.xpath(DESC_XPATH).get()
        price_text = sel.xpath(PRICE_XPATH).get()
        breadcrumbs = sel.xpath(BREADCRUMB_XPATH).getall()
        images = sel.xpath(IMAGE_XPATH).getall()
        json_scripts = sel.xpath(JSON_LD_XPATH).getall()

        # EXTRACT FROM JSON-LD
        json_data = {}
        for script in json_scripts:
            try:
                data = json.loads(script)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    json_data = data
                    break
                elif isinstance(data, dict) and data.get('mainEntity', {}).get('@type') == 'Product':
                    json_data = data['mainEntity']
                    break
            except json.JSONDecodeError:
                continue

    
        # CLEAN SECTION
        product_name = product_name.strip() if product_name else json_data.get('name', '')
        brand = brand.strip() if brand else (
            json_data.get('brand', {}).get('name') if isinstance(json_data.get('brand'), dict)
            else json_data.get('brand', '')
        )
        description = description.strip() if description else re.sub(
            '<[^<]+?>', '', json_data.get('description', '')
        ) if json_data.get('description') else ""

        price = ""
        if price_text:
            match = re.search(r'(\d+[\.,]\d{2})', price_text)
            price = match.group(1).replace(',', '.') if match else ""
        else:
            offers = json_data.get('offers', {})
            if isinstance(offers, dict):
                price = str(offers.get('price', ''))

        crumbs_clean = [x.strip() for x in breadcrumbs if x.strip()]
        breadcrumbs_joined = " > ".join(crumbs_clean) if crumbs_clean else ""

        img_clean = []
        if 'image' in json_data:
            imgs = json_data.get('image')
            if isinstance(imgs, list):
                img_clean = [x for x in imgs if isinstance(x, str)]
            elif isinstance(imgs, str):
                img_clean = [imgs]
        elif images:
            img_clean = [x for x in images]


        # ITEM YIELD SECTION 
        item = {}
        item["unique_id"] = product_id
        item["product_name"] = product_name
        item["brand"] = brand
        item["product_description"] = description
        item["selling_price"] = price
        item["currency"] = "EUR"
        item["breadcrumbs"] = breadcrumbs_joined
        item["pdp_url"] = url
        item["instock"] = True
        item["extraction_date"] = datetime.now(timezone.utc)
        item["image_url_1"] = img_clean[0] if len(img_clean) > 0 else ""
        item["image_url_2"] = img_clean[1] if len(img_clean) > 1 else ""
        item["image_url_3"] = img_clean[2] if len(img_clean) > 2 else ""
        item["producthierarchy_level1"] = crumbs_clean[0] if len(crumbs_clean) > 0 else ""
        item["producthierarchy_level2"] = crumbs_clean[1] if len(crumbs_clean) > 1 else ""
        item["producthierarchy_level3"] = crumbs_clean[2] if len(crumbs_clean) > 2 else ""
        item["producthierarchy_level4"] = crumbs_clean[3] if len(crumbs_clean) > 3 else ""
        item["producthierarchy_level5"] = crumbs_clean[4] if len(crumbs_clean) > 4 else ""
        item["producthierarchy_level6"] = crumbs_clean[5] if len(crumbs_clean) > 5 else ""
        item["producthierarchy_level7"] = crumbs_clean[6] if len(crumbs_clean) > 6 else ""


        try:
            product_doc = ProductItem(**item)
            product_doc.save()
        except Exception as e:
            logging.warning(f"Failed to save product {url}: {e}")


    def extract_product_id(self, url):
        """Extract product ID from URL"""
        match = re.search(r"/p/(B3-\w+)", url)
        return match.group(1) if match else url.split("/")[-1]


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()
