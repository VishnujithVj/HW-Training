import logging
import json
import time
from curl_cffi import requests
from pymongo import MongoClient
from parsel import Selector
from fuzzywuzzy import fuzz
from urllib.parse import quote_plus
from settings import (HEADERS, MONGO_URI, MONGO_DB,MONGO_COLLECTION_INPUT, MONGO_COLLECTION_MATCHED,SEARCH_BASE_URL, FUZZY_MATCH_THRESHOLD, EXACT_MATCH_SCORE,
    REQUEST_DELAY, REQUEST_TIMEOUT, BASE_URL)


class Crawler:
    """Crawling and matching products from El CorteIngles"""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(MONGO_URI)
        self.mongo = self.client[MONGO_DB]
        logging.info("MongoDB connection established successfully")


    def start(self):
        """Fetch all input items from MongoDB"""
        items = list(self.mongo[MONGO_COLLECTION_INPUT].find({}, {"_id": 0}))
        total_items = len(items)
        logging.info(f"Found {total_items} items to process")

        for idx, item in enumerate(items, 1):
            ean = str(item.get("EAN MASTER", "")).strip()
            input_name = str(item.get("PRODUCT GENERAL NAME", "")).strip()
            logging.info(f"[{idx}/{total_items}] Processing: {input_name}")

            meta = {
                "ean": ean,
                "input_name": input_name,
                "product_saved": False, 
                "index": idx,
                "total": total_items
            }

            """ EAN Search """
            if ean:
                q = quote_plus(ean)

                search_by_ean = f"{SEARCH_BASE_URL}?s={q}&stype=text_box"
                
                try:
                    response = requests.get(search_by_ean, headers=HEADERS, impersonate="chrome", timeout=REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        self.parse_item(response, meta, search_type="ean")
                    else:
                        logging.warning(f"EAN search failed with status {response.status_code}")
                except Exception as e:
                    logging.error(f"Error in EAN search: {str(e)}")
            
            """ Product Name Search """
            if not meta["product_saved"] and input_name:              
                q = quote_plus(input_name)

                search_by_name = f"{SEARCH_BASE_URL}?s={q}&stype=text_box"
                
                try:
                    response = requests.get(search_by_name, headers=HEADERS, impersonate="chrome", timeout=REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        self.parse_item(response, meta, search_type="name")
                    else:
                        logging.warning(f"Name search failed with status {response.status_code}")
                except Exception as e:
                    logging.error(f"Error in name search: {str(e)}")

            time.sleep(REQUEST_DELAY)
        logging.info("Crawler completed")


    def parse_item(self, response, meta, search_type):
        """Parse search results based on search type (EAN or Name)"""
        sel = Selector(response.text)

        """" XPATH """
        PRODUCT_XPATH = '//li[contains(@class,"products_list-item")]'
        URL_NAME_XPATH = './/a[contains(@class,"product_preview-title")]/@href'
        NAME_XPATH = './/a[contains(@class,"product_preview-title")]//text()'
        
        """EXTRACT"""
        products = sel.xpath(PRODUCT_XPATH)
        
        if search_type == "ean":
            """EAN search parsing"""
            ean = meta["ean"]
            
            if len(products) == 1:
                """Case A: Exactly one product found"""

                p = products[0]
                href = p.xpath(URL_NAME_XPATH).get()
                name = p.xpath(NAME_XPATH).get()
                
                if href and name:
                    """ITEM YEILD (EAN EXACT)"""
                    item = {}
                    item["match_type"] = "EAN EXACT"
                    item["ean"] = ean
                    item["product_name"] = name.strip()
                    item["product_url"] = BASE_URL.rstrip('/') + href
                    
                    logging.info(f"Saved via single EAN result: {name.strip()}")
                    meta["product_saved"] = True
                    try:
                        self.mongo[MONGO_COLLECTION_MATCHED].insert_one(item)
                    except Exception as e:
                        logging.error(f"Error saving EAN exact match: {str(e)}")
                        
            elif len(products) > 1:
                """Case B: Multiple products - check EAN in card text"""        
                matched = []
                
                for p in products:
                    card_text = " ".join(p.xpath(".//text()").getall()).upper()
                    
                    if ean in card_text:
                        href = p.xpath(URL_NAME_XPATH).get()
                        name = p.xpath(NAME_XPATH).get()
                        
                        if href and name:
                            """Item structure for EAN IN CARD"""
                            matched.append({
                                "match_type": "EAN IN CARD",
                                "ean": ean,
                                "product_name": name.strip(),
                                "product_url": BASE_URL.rstrip('/') + href
                            })
                
                if len(matched) == 1:
                    """ITEM YEILD (EAN IN CARD, unique)"""

                    item = matched[0]
                    logging.info("Saved via EAN found in exactly one card")
                    meta["product_saved"] = True
                    try:
                        self.mongo[MONGO_COLLECTION_MATCHED].insert_one(item)
                    except Exception as e:
                        logging.error(f"Error saving EAN card match: {str(e)}")
                else:
                    logging.warning("✘ EAN not uniquely identifiable in PLP")
        
        elif search_type == "name":
            """Name search parsing with fuzzy matching"""
            
            input_name = meta["input_name"]
            exact = None
            partial = []
            
            for p in products:
                name = p.xpath(NAME_XPATH).get()
                href = p.xpath(URL_NAME_XPATH).get()
                
                if not name or not href:
                    continue
                
                score = fuzz.token_sort_ratio(input_name.upper(), name.upper())
                
                if score == EXACT_MATCH_SCORE:
                    """Item structure for NAME EXACT"""
                    exact = {
                        "match_type": "NAME EXACT",
                        "score": score,
                        "product_name": name.strip(),
                        "product_url": BASE_URL.rstrip('/') + href
                    }
                    break
                    
                elif score >= FUZZY_MATCH_THRESHOLD:
                    """Item structure for NAME PARTIAL"""
                    partial.append({
                        "match_type": "NAME PARTIAL",
                        "score": score,
                        "product_name": name.strip(),
                        "product_url": BASE_URL.rstrip('/') + href
                    })
            
            if exact:
                """ITEM YEILD (NAME EXACT)"""
                item = exact
                logging.info("Saved exact name match")

                meta["product_saved"] = True
                try:
                    self.mongo[MONGO_COLLECTION_MATCHED].insert_one(item)
                except Exception as e:
                    logging.error(f"Error saving exact name match: {str(e)}")
                    
            elif partial:
                """ITEM YEILD (NAME PARTIALS)"""
                logging.info(f"Saved {len(partial)} partial name matches")
                meta["product_saved"] = True

                try:
                    self.mongo[MONGO_COLLECTION_MATCHED].insert_one(partial) 
                except Exception as e:
                    logging.error(f"Error saving partial name matches: {str(e)}")
            else:
                logging.warning("No name match found")

        if meta["product_saved"]:
            return True
        return False

    def close(self):
        self.client.close()
        logging.info("MongoDB connection closed")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()