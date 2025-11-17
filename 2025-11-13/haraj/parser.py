import logging
import random
import time
from curl_cffi import requests
from mongoengine import connect
from settings import MONGO_DB, MONGO_HOST
from items import PropertyItem, PropertyPostItem


def get_safe(data, *keys, default=""):
    for k in keys:
        data = data.get(k) if isinstance(data, dict) else None
        if data is None:
            return default
    return data


USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
]

IMPERSONATE = ["chrome110", "chrome111", "chrome112", "safari17", "safari16", "edge99"]

def new_session():
    """Create a fresh session with safe impersonation."""
    return requests.Session(
        headers={
            "accept": "application/json",
            "accept-language": "ar",
            "appverison": "7.2.83",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2OTFhZmNjNTQyYzdlMDZjZjQwMjQ2YjkiLCJyb2xlIjoiR1VFU1QiLCJzdGF0dXMiOiJERUFDVElWQVRFRCIsImlhdCI6MTc2MzM3NjMyNX0.TKwaBiMg1ANJkINiO1zl0ZxPaHbUBMp4vwSkSaow3sU",
            "cache-control": "no-cache",
            "origin": "https://dealapp.sa",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://dealapp.sa/",
            "sec-ch-ua": '"Google Chrome";v="141", "Not A Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": random.choice(USER_AGENTS),
        },
        impersonate=random.choice(IMPERSONATE),
        timeout=12
    )

def sleep_random():
    time.sleep(random.uniform(1.5, 4.5))

class Parser:
    """Extract and save property info from DealApp API"""
    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host=MONGO_HOST)
        self.session = new_session()
        logging.info("MongoDB connected")

    def rotate(self):
        logging.warning("Rotating session...")
        sleep_random()
        self.session = new_session()

    def start(self):
        posts = PropertyPostItem.objects()
        logging.info(f"Found {posts.count()} IDs")

        for post in posts:
            ad_id = getattr(post, "dealapp_ad_id", "")
            if not ad_id:
                logging.warning(f"No ad_id → {post.url}")
                continue
            self.parse_item(post, ad_id)
            sleep_random()


    def parse_item(self, post, ad_id):
        api_url = f"https://api.dealapp.sa/production/ad/{ad_id}"
        logging.info(f"GET {api_url}")

        haraj_url = getattr(post, "url", "")
        try:
            res = self.session.get(api_url)
        except Exception as e:
            logging.error(f"Request error for {ad_id}: {e}")
            self.rotate()
            return False

        if res.status_code >= 400:
            logging.error(f"HTTP {res.status_code} for {ad_id}")
            self.rotate()
            return False

        try:
            data = res.json().get("data", {})
        except Exception:
            logging.error(f"Invalid JSON for {ad_id}")
            self.rotate()
            return False

        item = {
            "reference_number": str(data.get("adLicenseNumber", "")),
            "property_id": str(data.get("code", "")),
            "url": haraj_url,
            "broker_display_name": str(data.get("advertiserName", "") or get_safe(data, "regaRawData", "advertiserName")),
            "category_name": "real-estate",
            "title": str(data.get("title", "")),
            "property_type": str(get_safe(data, "propertyType", "")),
            "description": str(data.get("description", "")),
            "location": str(data.get("locationDescriptionOnMOJDeed")
                or get_safe(data, "district","city", "name_ar")),
            "price": str(data.get("price", "")),
            "currency": "SAR",
            "price_per": str(data.get("propertyMeterPrice", "")),
            "rera_permit_number": str(data.get("brokerageAndMarketingLicenseNumber", "")),
            "amenities": data.get("propertyUtilities", []),
            "number_of_photos": len(get_safe(data, "media", "extra", default=[])),
            "phone_number": str(get_safe(data, "advertiser", "phone")),
        }
        """Save items"""
        try:
            PropertyItem(**item).save()
            logging.info(f"Saved: {ad_id}")
        except Exception as e:
            logging.error(f"Save error for {ad_id}: {e}")


    def close(self):
        logging.info("MongoDB closed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = Parser()
    parser.start()
    parser.close()

