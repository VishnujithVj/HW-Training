import logging
import random
import time
from curl_cffi import requests
from mongoengine import connect
from settings import MONGO_DB, MONGO_HOST
from items import PropertyItem, PropertyPostItem


def get_safe(data, *keys, default=""):
    for k in keys:
        if not isinstance(data, dict) or k not in data:
            return default
        data = data[k]
    return data


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
]

IMPERSONATE = ["chrome120", "chrome119", "chrome118", "firefox120", "firefox118"]

def new_session():
    return requests.Session(
        headers={
            "accept": "application/json",
            "accept-language": "ar",
            "appverison": "7.2.83",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2OTE1N2JlMjZmODBkYzUxNzBlYTA3MTEiLCJyb2xlIjoiR1VFU1QiLCJzdGF0dXMiOiJERUFDVElWQVRFRCIsImlhdCI6MTc2MzAxNTY1MH0.T76lmw8Q3tAKFGuLblcNvYsJ67Ln8fxoaXgxuzHL6eA",
            "origin": "https://dealapp.sa",
            "referer": "https://dealapp.sa/",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": random.choice(USER_AGENTS),
        },
        impersonate=random.choice(IMPERSONATE),
        timeout=12,
    )

class Parser:
    """Extract detailed property info from DealApp API"""
    def __init__(self):
        connect(alias="default", db=MONGO_DB, host=MONGO_HOST)
        self.session = new_session()
        logging.info("MongoDB connected")

    def rotate(self):
        logging.warning("Rotating session...")
        self.session = new_session()

    def start(self):
        posts = PropertyPostItem.objects()
        logging.info(f"Found {posts.count()} IDs")

        for post in posts:
            ad_id = getattr(post, "dealapp_ad_id", None)
            if ad_id:
                self.parse_item(ad_id)
                time.sleep(random.uniform(1.5, 3.2))
            else:
                logging.warning(f"No ad_id → {post.url}")

    def parse_item(self, ad_id):
        url = f"https://api.dealapp.sa/production/ad/{ad_id}"
        logging.info(f"GET {url}")

        try:
            res = self.session.get(url)
            if res.status_code >= 400:
                self.rotate()
                return False
            try:
                data = res.json().get("data", {})
            except:
                self.rotate()
                return False
        except Exception as e:
            logging.error(f"Error {ad_id}: {e}")
            self.rotate()
            return False

        if not data:
            logging.error(f"No data for {ad_id}")
            return False

        item = PropertyItem(
            reference_number=str(data.get("adLicenseNumber", "")),
            property_id=str(data.get("code", "")),
            url=url,
            broker_display_name=str(data.get("advertiserName", "")),
            category_name="real-estate",
            title=str(data.get("title", "")),
            property_type=str(get_safe(data, "propertyType", "propertyType")),
            description=str(data.get("description", "")),
            location=str(data.get("locationDescriptionOnMOJDeed") or get_safe(data, "city", "name_ar")),
            price=str(data.get("price", "")),
            currency="SAR",
            price_per=str(data.get("propertyMeterPrice", "")),
            rera_permit_number=str(data.get("brokerageAndMarketingLicenseNumber", "")),
            amenities=data.get("propertyUtilities", []),
            number_of_photos=len(get_safe(data, "media", "extra", default=[])),
            phone_number=str(get_safe(data, "advertiser", "phone")),
        )
        item.save()
        logging.info(f"Saved {ad_id}")
        return True

    def close(self):
        self.mongo.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = Parser()
    parser.start()
    parser.close()
