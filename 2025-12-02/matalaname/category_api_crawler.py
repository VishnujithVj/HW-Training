import logging
import time
import re
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from settings import MONGO_DB, BASE_URL
from items import CategoryItem  


class Crawler:
    """Crawling Categories"""
    
    def __init__(self):
        self.mongo = connect(db=MONGO_DB, alias='default', host='localhost', port=27017)
    
    def start(self):
        """Requesting Start url"""
        
        url=f"{BASE_URL}/ae_en"
        
        meta = {}
        meta['start_url'] = url
        
        try:
            response = requests.get(url, impersonate="chrome110", timeout=20)
            if response.status_code == 200:
                is_next = self.parse_item(response, meta)
                if not is_next:
                    logging.info("Category parsing completed")

        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")

    def parse_item(self, response, meta):
        """item part"""
        sel = Selector(response.text)
        
        # XPATH
        CATEGORY_XPATH = "//li[contains(@class,'categoryRoundWidget_tab_item__usuFC ')]/button"
        SUBCATEGORY_DIV_XPATH = "//div[@class='categoryRoundWidget_tab_content_item__WyDCH']"
        SUBCATEGORY_LINK_XPATH = "./a"
        SUBCATEGORY_HREF_XPATH = "@href"
        SUBCATEGORY_TEXT_XPATH = "normalize-space(.)"
        
        # EXTRACT
        category_nodes = sel.xpath(CATEGORY_XPATH)
        categories = [c.xpath("string()").get().strip().lower() for c in category_nodes]
        logging.info(f"Found {len(categories)} categories")
        
        # Extract subcategories
        subcategory_nodes = sel.xpath(SUBCATEGORY_DIV_XPATH)
        all_subcats = []
        for div in subcategory_nodes:
            for a in div.xpath(SUBCATEGORY_LINK_XPATH):
                href = a.xpath(SUBCATEGORY_HREF_XPATH).get()
                text = a.xpath(SUBCATEGORY_TEXT_XPATH).get(default="").strip().lower()
                if not href or not text:
                    continue
                full_href = BASE_URL + href if href.startswith("/") else href
                all_subcats.append({"name": text, "href": full_href})
        
        # Map subcategories to categories
        if categories:
            for category_name in categories:
                matched_subcats = []
                for sub in all_subcats:
                    if f"/{category_name}/" in sub["href"]:
                        matched_subcats.append({
                            "sub_category_name": sub["name"],
                            "sub_category_url": sub["href"]
                        })
                
                logging.info(f"Processing Category: {category_name}")
                
                # Process each subcategory
                for subcat in matched_subcats:
                    time.sleep(1)  # polite delay
                    uids = self.parse_uid(subcat["sub_category_url"])
                    
                    # ITEM YEILD
                    item = {}
                    item['category_name'] = category_name
                    item['sub_category_name'] = subcat["sub_category_name"]
                    item['sub_category_url'] = subcat["sub_category_url"]
                    item['uids'] = uids
                    logging.info(item)
                    try:
                        cat_item = CategoryItem(**item)
                        cat_item.save()
                    except Exception as e:
                        logging.warning(f"Mongo insert failed: {e}")
                
                logging.info(f"Completed Category: {category_name} with {len(matched_subcats)} subcategories")
            
            return True
        return False
    
    def parse_uid(self, sub_url):
        """Extract UID(s) from subcategory page"""
        try:
            response = requests.get(sub_url, impersonate="chrome110", timeout=20)
            if response.status_code != 200:
                logging.warning(f"Failed {response.status_code}: {sub_url}")
                return None
            
            sel = Selector(response.text)

            SCRIPT_XPATH = '//script[contains(text(),"categoryData")]/text()'
            
            script_text = sel.xpath(SCRIPT_XPATH).get()
            if not script_text:
                return None
            
            # Remove push wrapper
            payload = script_text.replace('self.__next_f.push([1,"1e:[[\"$\",\"$L1f\",null,', '')
            payload = payload.replace(']","$L21"])', '')
            
            # Decode escaped characters
            payload = payload.encode('utf-8').decode('unicode_escape')
            payload = payload.replace("\\/", "/")
            
            # Extract UID(s)
            uids = re.findall(r'"uid"\s*:\s*"([^"]+)"', payload)
            return uids if uids else None
            
        except Exception as e:
            logging.error(f"Error fetching {sub_url}: {e}")
            return None
    
    def close(self):
        """Close function for all module object closing"""
        logging.info("Matalanme Crawling Completed")
        self.mongo.close()
        


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()