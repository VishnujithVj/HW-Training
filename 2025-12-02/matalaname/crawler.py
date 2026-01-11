import logging
import time
import requests
from mongoengine import connect
from settings import MONGO_DB, HEADERS, QUERY, API_URL 
from items import ProductItem, CategoryItem


class Crawler:
    """Crawling Matalan products via GraphQL"""
    
    def __init__(self):
        self.mongo = connect(db=MONGO_DB, alias="default", host="localhost", port=27017)
    
    def start(self):
        """Requesting Start url"""
        
        categories = CategoryItem.objects()
        for cat in categories:
            if not cat.uids:
                continue
            
            for uid in cat.uids:
                logging.info(f"Processing UID: {uid}")
                meta = {}
                meta['category_name'] = cat.category_name
                meta['subcategory_name'] = cat.sub_category_name
                meta['category_uid'] = uid
                page = meta.get("page", 1)  
                # Fetch first page to get total pages
                variables = {
                    "filter": {"category_uid": {"in": [uid]}},
                    "pageSize": 40,
                    "currentPage": page,
                    "sort": {}
                }
                response = requests.post(API_URL, headers=HEADERS, json={"query": QUERY, "variables": variables})
                
                if response.status_code == 200:
                    data = response.json()
                    total_pages = data.get("data", {}).get("products", {}).get("page_info", {}).get("total_pages", 1)
                    
                    # Loop through all pages
                    while page <= total_pages:
                        if page > 1:
                            variables["currentPage"] = page
                            response = requests.post(API_URL, headers=HEADERS, json={"query": QUERY, "variables": variables})
                        
                        if response.status_code == 200:
                            is_next = self.parse_item(response, meta)
                            if not is_next:
                                logging.info("Pagination completed")
                                break
                            # pagination crawling
                            page += 1
                            meta["page"] = page
                            time.sleep(1.5)  
                       
                else:
                    logging.warning(f"Request failed for UID {uid}")
    
    def parse_item(self, response, meta):
        """item part"""
        data = response.json()
        items = data.get("data", {}).get("products", {}).get("items", [])
        
        if items:
            for product in items:
                # EXTRACT
                unique_id = product.get("id")
                name = product.get("name")
                url_key = product.get("url_key")
                image_url = product.get("thumbnail", {}).get("url")
                selling_price = product.get("price_range", {}).get("minimum_price", {}).get("final_price", {}).get("value")
                regular_price = product.get("price_range", {}).get("minimum_price", {}).get("regular_price", {}).get("value")
     
                # Construct breadcrumbs
                category_name = meta.get("category_name", "").title()
                subcategory_name = meta.get("subcategory_name", "").title()
                breadcrumbs = f"Home / {category_name} / {subcategory_name} / {name}"
                
                # ITEM YEILD
                item = {}
                item['unique_id'] = unique_id
                item['product_name'] = name
                item['url_key'] = url_key
                item['image'] = image_url
                item['selling_price'] = selling_price
                item['regular_price'] = regular_price
                item['breadcrumbs'] = breadcrumbs
                logging.info(item)
                try:
                    product_item = ProductItem(**item)
                    product_item.save()
                except Exception as e:
                    logging.warning(f"Mongo insert failed: {e}")
            
            return True
        return False
    
    def close(self):
        """Close function for all module object closing"""
        logging.info("Product crawling completed.")
        self.mongo.close()
        


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()