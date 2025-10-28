import logging
import requests
import time
from mongoengine import connect
from items import QatarLivingPropertyItem, ProductFailedItem
from settings import HEADERS, MONGO_DB, PROPERTIES_BASE_URL, PER_PAGE, CATEGORIES


class Parser:
    """parser"""

    def __init__(self):
        self.session = requests.Session()
        self.initialize_mongo_connection()
        
    def initialize_mongo_connection(self):
        """Initialize MongoDB connection for MongoEngine"""

        connect(db=MONGO_DB, alias='default', host='mongodb://localhost:27017/')
        logging.info(f"MongoDB connected to database: {MONGO_DB}")
        return True

    def start(self):
        """start code - Parse all properties directly from API"""
        logging.info("Starting to parse properties from API...")
        
        # Track failed API calls
        failed_categories = []
        
        for category in CATEGORIES:
            logging.info(f"Parsing category {category}...")
            page = 1
            category_failed = False
            
            while True:
                try:
                    params = {
                        "category": category,
                        "cur_page": page,
                        "per_page": PER_PAGE
                    }

                    response = self.session.get(PROPERTIES_BASE_URL, params=params, headers=HEADERS, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        ads = data.get("ads", [])
                        meta = data.get("meta", {})

                        if not ads:
                            logging.info(f"No more ads found for category {category}")
                            break

                        """Process all ads in this page"""
                        ads_processed = 0
                        for ad in ads:
                            if self.process_ad_data(ad, category):
                                ads_processed += 1

                        total_pages = meta.get("totalPages", 1)
                        logging.info(f"Processed page {page}/{total_pages} for category {category} - {ads_processed} ads saved")

                        if page >= total_pages:
                            break
                        page += 1
                        time.sleep(1) 
                    else:
                        logging.error(f"API error for category {category} page {page}: Status {response.status_code}")
                        self.save_failed_url(f"Category {category} page {page}", f"HTTP {response.status_code}")
                        category_failed = True
                        break

                except Exception as e:
                    logging.error(f"Error processing category {category} page {page}: {e}")
                    self.save_failed_url(f"Category {category} page {page}", str(e))
                    category_failed = True
                    break

            if category_failed:
                failed_categories.append(category)

        # Save failed categories summary
        if failed_categories:
            self.save_failed_url(f"Failed categories: {failed_categories}", "Category parsing failed")
        
        logging.info("Property parsing completed")
        if failed_categories:
            logging.warning(f"Failed to parse categories: {failed_categories}")

    def process_ad_data(self, ad, category_id):
        """Process individual ad data and save to MongoDB"""
        
        try:
            ad_id = ad.get("adId")
            if not ad_id:
                logging.warning(f"Ad missing ID, skipping...")
                return False

            """Check if ad already exists"""
            existing_ad = QatarLivingPropertyItem.objects(unique_id=str(ad_id)).first()
            if existing_ad:
                logging.debug(f"Ad {ad_id} already exists, skipping...")
                return False

            """Build the URL from the API data"""
            url_path = ad.get('urls', [{}])[0].get('urlAlias', '')
            url = f"https://qlp.qatarliving.com{url_path}" if url_path else ""

            item = QatarLivingPropertyItem(
                unique_id=str(ad_id),
                url=url,
                title=ad.get("title", "").strip(),
                price=str(ad.get("price", "")),
                bedroom=ad.get("bedroom", {}).get("name", ""),
                bathroom=ad.get("bathroom", {}).get("name", ""),
                furnishing=ad.get("furnishing", {}).get("name", ""),
                property_type=ad.get("propertyType", {}).get("name", ""),
                square_meters=str(ad.get("squareMeters", "")),
                country=ad.get("location", {}).get("country", {}).get("name", ""),
                city=ad.get("location", {}).get("city", {}).get("name", ""),
                agent_name=ad.get("user", {}).get("name", ""),
                company=ad.get("companyUser", {}).get("name", ""),
                images=[
                    f"https://qlp.qatarliving.com/{img.get('uri')}"
                    for img in ad.get("images", [])
                    if img.get("uri")
                ],
                category_id=category_id
            )

            item.save()
            logging.info(f"Saved ad: {ad_id} - {ad.get('title', '')}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving ad {ad.get('adId', 'unknown')}: {e}")

            """Save failed ad URL if available"""
            url_path = ad.get('urls', [{}])[0].get('urlAlias', '')
            if url_path:
                failed_url = f"https://qlp.qatarliving.com{url_path}"
                self.save_failed_url(failed_url, f"Failed to save ad: {str(e)}")
            return False

    def save_failed_url(self, url, error_message=""):
        """Save failed URL to ProductFailedItem collection"""
        failed_item = ProductFailedItem(
            url=url,
            error_message=error_message
        )
        failed_item.save()
        logging.error(f"Saved failed URL: {url} - Error: {error_message}")

    def close(self):
        """connection close"""
        self.session.close()


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()