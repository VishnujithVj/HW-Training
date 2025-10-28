import logging
import requests
import time
from mongoengine import connect
from items import ProductCategoryUrlItem, ProductUrlItem
from settings import HEADERS, MONGO_DB, PROPERTIES_BASE_URL, PER_PAGE, CATEGORIES


class Crawler:
    """Crawling Urls"""

    def __init__(self):
        self.session = requests.Session()
        self.initialize_mongo_connection()
        
    def initialize_mongo_connection(self):
        """Initialize MongoDB connection for MongoEngine"""
    
        connect(db=MONGO_DB, alias='default', host='mongodb://localhost:27017/')
        logging.info(f"MongoDB connected to database: {MONGO_DB}")
        return True


    def start(self):
        """Requesting Start url"""

        logging.info("Qatar Living Properties Crawlering")

        for category in CATEGORIES:
            logging.info(f"🔹 Crawling category {category}...")
            page = 1

            # Save category URL
            category_url = f"{PROPERTIES_BASE_URL}?category={category}"
            category_item = ProductCategoryUrlItem(
                url=category_url,
                category_id=category
            )
            category_item.save()
            logging.info(f"Saved category URL: {category_url}")

            while True:
                params = {
                    "category": category,
                    "cur_page": page,
                    "per_page": PER_PAGE
                }

                try:
                    response = self.session.get(PROPERTIES_BASE_URL, params=params, headers=HEADERS, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        ads = data.get("ads", [])
                        meta = data.get("meta", {})

                        if not ads:
                            logging.warning(f"No ads found for category={category} page={page}")
                            break

                        for ad in ads:
                            ad_id = ad.get("adId")
                            url_path = ad.get('urls', [{}])[0].get('urlAlias', '')
                            url = f"https://qlp.qatarliving.com{url_path}" if url_path else ""
                            
                            if ad_id and url:
                                # Save product URL
                                product_url_item = ProductUrlItem(url=url)
                                product_url_item.save()
                                logging.info(f"Saved URL: {url} | adId: {ad_id} | category: {category}")

                        total_pages = meta.get("totalPages", 1)
                        logging.info(f"Page {page}/{total_pages} done for category {category}")

                        if page >= total_pages:
                            break
                        page += 1
                        time.sleep(1) 
                    else:
                        logging.error(f"Error fetching category={category} page={page}: Status {response.status_code}")
                        break

                except Exception as e:
                    logging.error(f"Error fetching category={category} page={page}: {e}")
                    break

        logging.info("URL crawling completed")

    def close(self):
        """Close function for all module object closing"""
        self.session.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()