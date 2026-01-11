import re
import logging
import requests
from parsel import Selector
from datetime import datetime
from pymongo import MongoClient
from settings import HEADERS, MONGO_DB, MONGO_COLLECTION_DATA, MONGO_COLLECTION_URL, MONGO_COLLECTION_URL_FAILED


class Parser:

    def __init__(self):
        self.client = MongoClient("localhost", 27017)
        self.mongo = self.client[MONGO_DB]
        logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s")

    """ RETRY REQUEST FUNCTION """
    def fetch_with_retry(self, url, retries=3):
        for attempt in range(1, retries + 1):
            try:
                logging.info(f"Fetching → {url}  (Attempt {attempt})")
                response = requests.get(url, headers=HEADERS, timeout=20)
                if response.status_code == 200:
                    return response
                else:
                    logging.warning(f"Status {response.status_code}, retrying...")
            except Exception as e:
                logging.error(f"Request error: {e}, retrying...")

        return None

    def start(self):
        metas = list(self.mongo[MONGO_COLLECTION_URL].find({},
                    {"url": 1, "category": 1}))

        if not metas:
            logging.warning("No product URLs found in database!")
            return

        for meta in metas:
            url = meta.get("url")
            category_url = meta.get("category")

            if not url:
                logging.warning("Empty URL — skipping")
                continue

            """RETRYING"""
            response = self.fetch_with_retry(url)

            if response:
                try:
                    self.parse_item(url, response, category_url)
                except Exception as e:
                    logging.error(f"Parsing failed → {url} : {e}")
            else:
                logging.error(f"Failed after retries → {url}")
                try:
                    self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one({
                        "url": url,
                        "status_code": "failed after retries"
                    })
                except Exception as e:
                    logging.error(f"Failed to log failed URL: {e}")

    def parse_item(self, url, response, category_url):
        try:
            select = Selector(text=response.text)
            html = response.text

            """ XPATH """
            TITLE_XPATH = '//div[contains(@class,"_title")]//h1/text()'
            DESC_XPATH = '//div[contains(@class,"_card__nZw1i")]//div[contains(@class,"_root__lFkcr")]//text()'
            PRICE_XPATH = '//div[contains(@class,"_pricing")]//h2/span/text()'
            BEDROOMS_XPATH = '//*[contains(text(),"غرف النوم")]/following::div[1]//text()'
            PUBLISHED_XPATH = '//span[contains(text(),"تاريخ الإضافة")]/following-sibling::span/text()'
            CATEGORY_XPATH = '//div[contains(@class,"_auction")]//h2/text()'
            DETAILS_XPATH = '//div[contains(@class, "_newSpecCard")]//div[contains(@class, "_item___")]'
            AMENITIES_XPATH = '//div[contains(@class,"_boolean__")]/div[contains(@class,"_label")]'
            PHOTOS_COUNT_XPATH = '//button[contains(@class,"_more__")]'
            BROKER_NAME_XPATH = '//h2[contains(@class,"_companyName")]/text()'
            AGENT_NAME_XPATH = '//h2[contains(@class,"_name")]/text()'

            """ EXTRACT """
            title = select.xpath(TITLE_XPATH).get() or ""
            desc_nodes = select.xpath(DESC_XPATH).getall()
            raw_desc = " ".join([d.strip() for d in desc_nodes if d.strip()])
            price = select.xpath(PRICE_XPATH).get()
            bedrooms = select.xpath(BEDROOMS_XPATH).get()
            published_at_raw = select.xpath(PUBLISHED_XPATH).get()
            category_raw = select.xpath(CATEGORY_XPATH).get()
            photos_raw = select.xpath(PHOTOS_COUNT_XPATH).xpath('string()').get()
            agent_name = select.xpath(AGENT_NAME_XPATH).get() or ""
            broker_name = select.xpath(BROKER_NAME_XPATH).get() or ""
            broker_display = broker_name.upper()
            

            """CLEAN """
            price = price.replace(",", "") if price else None
            description = re.sub(r"المزيد$", "", raw_desc).strip()
            description = re.sub(r"\s*\n\s*", " ", description)
            description = re.sub(r"\s+", " ", description)
            description = re.sub(r"[^\w\s\u0600-\u06FF.,!?/:()\-]", "", description)
            description = description.strip()

            """ Location """
            loc_match = re.search(r'"streetAddress"\s*:\s*"([^"]+)"', html)
            location = loc_match.group(1).strip() if loc_match else ""

            """ Bathrooms """
            bathrooms_match = re.search(r'"name"\s*:\s*"عدد دورات المياه"\s*,\s*"value"\s*:\s*("?)(\d+)\1', html)
            bathrooms = bathrooms_match.group(2) if bathrooms_match else ""

            """ Details dict """
            details = {}
            for box in select.xpath(DETAILS_XPATH):
                key = box.xpath('.//div[contains(@class,"_label")]/text()').get()
                value = box.xpath('.//div[contains(@class,"_value")]/text()').get()
                if key and value:
                    details[key.strip()] = value.strip()

            """ Extract number of photos """
            photos_count = ""
            if photos_raw:
                match = re.search(r'\(\s*(\d+)\s*\)', photos_raw)
                if match:
                    photos_count = int(match.group(1))

            """ Sub-Category 1 """
            purpose = details.get("الغرض", "")
            if "سكني" in purpose:
                sub_category_1 = "residential"
            elif "تجاري" in purpose:
                sub_category_1 = "commercial"
            else:
                sub_category_1 = ""

            """ Amenities """
            amenities = []
            for a in select.xpath(AMENITIES_XPATH):
                txt = "".join(a.xpath('.//text()').getall()).strip()
                if txt:
                    amenities.append(txt)

            """ Furnished """
            furnished = ""
            for a in amenities:
                if "Furnished" in a:
                    furnished = "furnished"
                    break
                if "مؤثثة" in a or "مؤثث" in a:
                    furnished = "مؤثثة"
                    break

            """ Category type """
            cat_clean = category_raw.strip() if category_raw else ""
            if "للبيع" in cat_clean:
                category = "sale"
            elif "للإيجار" in cat_clean:
                category = "rent"
            else:
                category = ""

            """ Property Type """
            text = cat_clean.replace("مزاد:", "").strip()
            parts = text.split()
            property_type = parts[0] if parts else ""

            """ ID and Reference """
            ref_match = re.search(r'\\"id\\"\s*:\s*(\d+)', html)
            reference = ref_match.group(1) if ref_match else ""

            """ Published date """
            published_at = ""
            if published_at_raw:
                try:
                    published_at = datetime.strptime(
                        published_at_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    published_at = ""

            iteration_number = datetime.now().strftime("%Y_%m")


            """ITEM YIELD """
            item = {}
            item["id"] = reference
            item["reference_number"] = reference
            item["url"] = url
            item["broker_display_name"] = broker_display
            item["broker"] = broker_name
            item["category"] = category
            item["category_url"] = category_url
            item["title"] = title
            item["description"] = description
            item["location"] = location
            item["price"] = price
            item["currency"] = "SAR"
            item["bedrooms"] = bedrooms
            item["bathrooms"] = bathrooms
            item["furnished"] = furnished
            item["scraped_ts"] = datetime.now().strftime("%Y-%m-%d")
            item["amenities"] = amenities
            item["details"] = details
            item["agent_name"] = agent_name
            item["number_of_photos"] = photos_count
            # item["phone_number"] = ""
            item["date"] = datetime.now().strftime("%Y-%m-%d")
            item["iteration_number"] = iteration_number
            item["property_type"] = property_type
            item["sub_category_1"] = sub_category_1
            # item["sub_category_2"] = sub_category_2
            item["published_at"] = published_at

            logging.info(item)

            try:
                self.mongo[MONGO_COLLECTION_DATA].insert_one(item)
            except Exception as e:
                logging.error(f"Mongo Insert Failed: {e}")

        except Exception as e:
            logging.error(f"Parse crashed: {e}")

    def close(self):
        self.client.close()
        logging.info("Parser finished.")


if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()


