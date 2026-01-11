import logging
import re
import json
import time
import requests
from datetime import datetime, timezone
from parsel import Selector
from mongoengine import connect
from settings import MONGO_DB, BASE_URL, PARSER_API_URL, PARSER_HEADERS, PARSER_QUERY
from items import ProductItem, ProductDetailItem, ProductFailedItem


class Parser:
    """Crawling Product Details"""
    
    def __init__(self):
        self.mongo = connect(db=MONGO_DB, alias="default", host="localhost", port=27017)
    
    def start(self):
        """Requesting Start url"""
        
        products = ProductItem.objects()
        logging.info(f"Found {products.count()} products to parse")
        
        for product in products:
            meta = {}
            meta['product'] = product
            url = f"{BASE_URL}/ae_en/{product.url_key}"
            logging.info(f"Processing: {url}")
            
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    is_next = self.parse_item(response, meta)
                    if not is_next:
                        logging.warning(f"No data found for {url}")
                    time.sleep(1)  
                else:
                    logging.warning(f"Non-200 status for {url}: {response.status_code}")
                    
                    ProductFailedItem(url=url).save()
                    logging.info(f"Saved failed URL: {url}")
                    
            except Exception as e:
                logging.error(f"Error processing {url}: {e}")
    
    def parse_item(self, response, meta):
        """item part"""
        product = meta.get('product')
        url = f"{BASE_URL}/ae_en/{product.url_key}"
        
        sel = Selector(response.text)
        """XPATH"""
        SCRIPT_XPATH = '//script[contains(text(),"Specifications")]/text()'
        """EXTRACT"""
        script_text = sel.xpath(SCRIPT_XPATH).get()
        
        if script_text:
            # Extract JSON inside self.__next_f.push([...])
            match = re.search(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', script_text)
            if match:
                json_str = match.group(1)
                # Decode escaped characters
                json_str = json_str.encode('utf-8').decode('unicode_escape')
                
                try:
                    data = json.loads(json_str)
                    
                    # EXTRACT
                    specifications = {}
                    description = ""
                    
                    for section in data:
                        title = section.get("title")
                        if title == "Specifications":
                            for child in section.get("children", []):
                                specifications[child.get("label")] = child.get("value")
                        elif title == "Description":
                            description = section.get("value", "").strip()
                    
                    # Fetch size and color using extra API
                    size, color = self.parse_size_color(product.url_key)
                    gender = specifications.get('Gender')
                    print(gender)
                    
                    # ITEM YEILD
                    item = {}
                    item['unique_id'] = product.unique_id
                    item['url'] = url
                    item['product_name'] = product.product_name
                    item['product_details'] = specifications
                    item['color'] = color
                    item['size'] = size
                    item['selling_price'] = product.selling_price
                    item['regular_price'] = product.regular_price
                    item['image'] = product.image
                    item['description'] = description
                    item['currency'] = 'AED'
                    item['gender'] = gender
                    item['breadcrumbs'] = product.breadcrumbs
                    item['extraction_date'] = datetime.now().strftime("%Y-%m-%d")
                                       
                    
                    logging.info(item)
                    try:
                        detail_item = ProductDetailItem(**item)
                        detail_item.save()
                    except Exception as e:
                        logging.warning(f"Mongo insert failed: {e}")
                    
                    return True
                except Exception as e:
                    logging.warning(f"JSON decode error for {url}: {e}")
        
        return False
    
    def parse_size_color(self, url_key):
        """Make an API call to fetch size and color variant options for a product"""
        variables = {"url_key": url_key}
        payload = {"query": PARSER_QUERY, "variables": json.dumps(variables), "operationName": "GetProductVarientOptions"}
        
        try:
            response = requests.get(PARSER_API_URL, headers=PARSER_HEADERS, params=payload, timeout=10)
            if response.status_code != 200:
                logging.warning(f"Variant API request failed for {url_key}")
                return None, None
            
            data = response.json()
            item = data.get("data", {}).get("products", {}).get("items", [])
            if not item:
                return None, None
            
            options = item[0].get("selected_variant_options", [])
            size = None
            color = None
            for opt in options:
                if opt.get("code") == "size":
                    size = opt.get("label")
                elif opt.get("code") == "color":
                    color = opt.get("label")
            
            return size, color
        
        except Exception as e:
            logging.error(f"Error fetching variant options for {url_key}: {e}")
            return None, None
    
    def close(self):
        """Close function for all module object closing"""
        logging.info("Product detail crawling completed.")
        self.mongo.close()
        

if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()