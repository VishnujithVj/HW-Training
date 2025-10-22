import logging
import requests
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urljoin
from parsel import Selector
from items import ProductData, ProductUrlItem
from settings import HEADERS, BASE_URL

class Parser:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def start(self, limit=None):
        """Start parsing process"""
        urls_to_parse = ProductUrlItem.objects()
        if limit:
            urls_to_parse = urls_to_parse[:limit]
            
        logging.info(f"Found {urls_to_parse.count()} URLs to parse")
        
        for i, url_item in enumerate(urls_to_parse, 1):
            logging.info(f"[{i}/{urls_to_parse.count()}] Parsing: {url_item.url}")
            self.parse_product(url_item.url)
            time.sleep(1)
        
        logging.info("Parsing completed")

    def parse_product(self, url):
        """Parse single product"""
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                self.extract_product_data(url, response.text)
            else:
                logging.error(f"Failed to fetch {url}: {response.status_code}")
        except Exception as e:
            logging.error(f"Error parsing {url}: {e}")

    def extract_product_data(self, url, html_content):
        sel = Selector(html_content)
        product_id = self.extract_product_id(url)
        
        if ProductData.objects(unique_id=product_id).first():
            logging.info(f"Product {product_id} already exists")
            return


        product = ProductData()
        product.unique_id = product_id
        product.pdp_url = url
        product.competitor_name = "BIPA"
        product.store_name = "BIPA Online"
        product.extraction_date = datetime.now(timezone.utc)
        product.product_unique_key = f"{product_id}P"
        product.currency = "EUR"
        product.instock = True

        """Get data from JSON-LD script tags"""
        self.get_json_ld_data(sel, product)

        """Get data from HTML tags for missing fields"""
        self.get_html_data(sel, product)

        try:
            product.save()
            logging.info(f"Saved: {product.product_name}")
        except Exception as e:
            logging.error(f"Failed to save {product_id}: {e}")

    def get_json_ld_data(self, sel, product):
        scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
        
        for script in scripts:
            try:
                data = json.loads(script)
                
                product_data = None
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    product_data = data
                elif isinstance(data, dict) and data.get('mainEntity') and data['mainEntity'].get('@type') == 'Product':
                    product_data = data['mainEntity']
                
                if product_data:

                    if not product.product_name:
                        product.product_name = product_data.get('name', '')
                    
                    # Brand
                    if not product.brand:
                        brand = product_data.get('brand', '')
                        if isinstance(brand, dict):
                            product.brand = brand.get('name', '')
                        else:
                            product.brand = brand
                    
                    # Description
                    if not product.product_description:
                        desc = product_data.get('description', '')
                        if desc:
                            product.product_description = re.sub('<[^<]+?>', '', desc)
                    
                    # Price
                    if not product.selling_price:
                        offers = product_data.get('offers', {})
                        if isinstance(offers, dict):
                            price = offers.get('price')
                            if price:
                                product.selling_price = str(price)
                    
                    # Ratings
                    if not product.rating or not product.review:
                        rating = product_data.get('aggregateRating', {})
                        if isinstance(rating, dict):
                            if not product.rating:
                                product.rating = str(rating.get('ratingValue', ''))
                            if not product.review:
                                product.review = str(rating.get('reviewCount', ''))
                    
                    # barcode and competitor product key
                    if not product.barcode:
                        product.barcode = product_data.get('mpn', '')
                    if not product.competitor_product_key:
                        product.competitor_product_key = product_data.get('sku', '')
                    
                    # Size
                    if not product.size:
                        size = product_data.get('size', '')
                        if size:
                            product.size = size
            
                            match = re.search(r'(\d+)\s*(ml|g|l|kg)', size, re.IGNORECASE)
                            if match:
                                product.grammage_quantity = match.group(1)
                                product.grammage_unit = match.group(2).lower()
                                if match.group(2).lower() in ['ml', 'l']:
                                    product.netcontent = size
                                else:
                                    product.netweight = size
                    
                    # Images from JSON-LD
                    images = product_data.get('image', [])
                    if isinstance(images, list):
                        for i, img in enumerate(images[:3]):
                            if isinstance(img, str):
                                setattr(product, f'image_url_{i+1}', img)
                    elif isinstance(images, str):
                        product.image_url_1 = images
                    
                    break 
                        
            except json.JSONDecodeError:
                continue

    def get_html_data(self, sel, product):
        """Get data from HTML tags"""
    
        if not product.product_name:
            name = sel.xpath('//h1//text()').get()
            if name:
                product.product_name = name.strip()

        # Brand from meta tag
        if not product.brand:
            brand = sel.xpath('//meta[@property="product:brand"]/@content').get()
            if brand:
                product.brand = brand.strip()

        # Description from meta tag
        if not product.product_description:
            desc = sel.xpath('//meta[@name="description"]/@content').get()
            if desc:
                product.product_description = desc.strip()

        # Price from HTML
        if not product.selling_price:
            price_text = sel.xpath('//span[contains(@class, "price")]//text()').get()
            if price_text:
                match = re.search(r'(\d+[\.,]\d{2})', price_text)
                if match:
                    product.selling_price = match.group(1).replace(',', '.')

        # Breadcrumbs
        breadcrumbs = sel.xpath('//nav[contains(@aria-label, "breadcrumb")]//a//text()').getall()
        if breadcrumbs:
            clean_crumbs = [b.strip() for b in breadcrumbs if b.strip()]
            product.breadcrumb = " > ".join(clean_crumbs)
    
            for i in range(1, 8):
                if i <= len(clean_crumbs):
                    setattr(product, f'producthierarchy_level{i}', clean_crumbs[i-1])

        # Additional details
        details_text = " ".join(sel.xpath('//div[contains(@class, "chakra-accordion")]//text()').getall())
        self.extract_from_text(details_text, product)

        # Images from HTML
        if not product.image_url_1:
            images = sel.xpath('//img[contains(@class, "product")]/@src').getall()
            for i, img in enumerate(images[:3]):
                if img:
                    full_url = urljoin(BASE_URL, img)
                    setattr(product, f'image_url_{i+1}', full_url)
                    setattr(product, f'file_name_{i+1}', img.split('/')[-1])

    def extract_from_text(self, text, product):
        """Extract product details from text content"""
        
        # Ingredients
        if not product.ingredients:
            if 'Ingredients:' in text:
                parts = text.split('Ingredients:')
                if len(parts) > 1:
                    product.ingredients = parts[1].split('.')[0].strip()
            elif 'Inhaltsstoffe:' in text:
                parts = text.split('Inhaltsstoffe:')
                if len(parts) > 1:
                    product.ingredients = parts[1].split('.')[0].strip()

        # Country of origin
        if not product.country_of_origin:
            if 'Countries of origin:' in text:
                parts = text.split('Countries of origin:')
                if len(parts) > 1:
                    product.country_of_origin = parts[1].split()[0].strip()
            elif 'Herkunftsländer:' in text:
                parts = text.split('Herkunftsländer:')
                if len(parts) > 1:
                    product.country_of_origin = parts[1].split()[0].strip()

        # Instructions for use
        if not product.instructionforuse:
            if 'Directions for use:' in text:
                parts = text.split('Directions for use:')
                if len(parts) > 1:
                    product.instructionforuse = parts[1].split('.')[0].strip()
            elif 'Verwendungshinweis:' in text:
                parts = text.split('Verwendungshinweis:')
                if len(parts) > 1:
                    product.instructionforuse = parts[1].split('.')[0].strip()

        # Net content
        if not product.netcontent:
            if 'Net content:' in text:
                parts = text.split('Net content:')
                if len(parts) > 1:
                    product.netcontent = parts[1].split()[0] + parts[1].split()[1]
            elif 'Nettogehalt:' in text:
                parts = text.split('Nettogehalt:')
                if len(parts) > 1:
                    product.netcontent = parts[1].split()[0] + parts[1].split()[1]

        # Net weight
        if not product.netweight:
            if 'Gross weight:' in text:
                parts = text.split('Gross weight:')
                if len(parts) > 1:
                    product.netweight = parts[1].split()[0] + parts[1].split()[1]
            elif 'Bruttogewicht:' in text:
                parts = text.split('Bruttogewicht:')
                if len(parts) > 1:
                    product.netweight = parts[1].split()[0] + parts[1].split()[1]

        # Packaging
        if not product.packaging:
            if 'Packaging:' in text:
                parts = text.split('Packaging:')
                if len(parts) > 1:
                    product.packaging = parts[1].split('.')[0].strip()
            elif 'Verpackung:' in text:
                parts = text.split('Verpackung:')
                if len(parts) > 1:
                    product.packaging = parts[1].split('.')[0].strip()

    def extract_product_id(self, url):
        """Extract product ID from URL"""
        match = re.search(r'/p/(B3-\w+)', url)
        return match.group(1) if match else url.split('/')[-1]

    def close(self):
        self.session.close()


if __name__ == "__main__":
    parser = Parser()
    parser.start(limit=10)
    parser.close()


