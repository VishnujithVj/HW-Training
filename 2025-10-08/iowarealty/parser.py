import logging
import time
import re
from curl_cffi import requests
from lxml import html
from mongoengine import Document, StringField, ListField, connect
from settings import HEADERS
from items import AgentItem

# ---------------- CONFIG ----------------
SCRAPER_API_KEY = "4bcb477d347c709f9d03a49c2246bf47"
SCRAPER_API_URL = "https://api.scraperapi.com"

# ---------------- MONGO CONNECTION ----------------
connect(db="iowarealty_db", host="mongodb://localhost:27017/iowarealty_db", alias="default")


# ---------------- MODELS ----------------
class AgentURLs(Document):
    _id = StringField(primary_key=True, default="agents")
    urls = ListField(StringField())
    meta = {"collection": "iowarealty_urls"}


class FailedURL(Document):
    profile_url = StringField(required=True, unique=True)
    reason = StringField()
    meta = {"collection": "iowarealty_failed"}


# ---------------- PARSER ----------------
class Parser:
    """Extract and store agent details"""

    def fetch_with_scraperapi(self, target_url: str) -> str:
        params = {
            "api_key": SCRAPER_API_KEY,
            "url": target_url,
            "country_code": "us",
        }
        try:
            resp = requests.get(SCRAPER_API_URL, params=params, headers=HEADERS, impersonate="chrome", timeout=30)
            if resp.status_code == 200:
                return resp.text
            raise Exception(f"HTTP {resp.status_code}")
        except Exception as e:
            raise Exception(f"ScraperAPI error: {e}")

    def start(self):
        agents_doc = AgentURLs.objects.first()
        urls = agents_doc.urls if agents_doc else []
        logging.info(f"Found {len(urls)} profiles to parse")

        for url in urls:
            try:
                html_text = self.fetch_with_scraperapi(url)
                self.parse_item(url, html_text)
                logging.info(f"Parsed {url}")
            except Exception as e:
                FailedURL.objects(profile_url=url).update_one(set__reason=str(e), upsert=True)
                logging.error(f"Failed {url}: {e}")
            time.sleep(2)

    def parse_item(self, profile_url, html_text):
        tree = html.fromstring(html_text)

        def x(xpath, default=""):
            val = tree.xpath(xpath)
            return val[0].strip() if val and isinstance(val[0], str) else default

        name_full = x('//section[contains(@class,"rng-bio-account-content-office")]//h1/text()')
        name_parts = name_full.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        middle_name = name_parts[1] if len(name_parts) == 3 else ""
        last_name = name_parts[-1] if len(name_parts) >= 2 else ""

        title = x('//section[contains(@class,"rng-bio-account-content-office")]//span[1]/text()')

        image_style = x('//div[contains(@class,"site-account-image")]/@style')
        image_url_match = re.search(r'url\((.*?)\)', image_style)
        image_url = image_url_match.group(1).strip() if image_url_match else ""

        office_section = " ".join(tree.xpath('//section[contains(@class,"rng-bio-account-content-office")]//div/text()'))
        office_section = re.sub(r'\s+', ' ', office_section).strip()

        office_name = ""
        address = ""
        zipcode = ""

        if office_section:
            parts = office_section.split("|", 1)
            if len(parts) == 2:
                office_name = parts[0].strip()
                address = parts[1].strip()
            else:
                address = office_section.strip()

            zip_match = re.search(r"\b\d{5}(?:-\d{4})?\b", address)
            if zip_match:
                zipcode = zip_match.group(0)

        agent_phone_numbers = [
            p.strip() for p in tree.xpath('//section[contains(@class,"rng-bio-account-details")]//a[contains(@href,"tel:")]/text()')
            if p.strip()
        ]

        desc_nodes = tree.xpath('//section[contains(@class,"rng-bio-account-content-description")]//div[@id="bioAccountContentDesc"]//text()')
        description = " ".join([d.strip() for d in desc_nodes if d.strip()])
        description = re.sub(r'\s+', ' ', description).strip()

        social_links = {}
        for li in tree.xpath('//ul[contains(@class,"rng-agent-bio-content-contact-social")]/li'):
            cls_list = li.xpath('./@class')
            cls = cls_list[0] if cls_list else ""
            link = x('.//a/@href')
            if cls and link:
                platform = cls.replace("social-", "").strip().lower()
                social_links[platform] = link

        languages = [
            l.strip() for l in tree.xpath('//section[contains(@class,"rng-bio-account-languages")]//div/text()')
            if l.strip() and l.strip().lower() != "languages"
        ]

        country = "USA"
        state = "IA"

        city_match = re.search(r"\b([A-Za-z]+)\s+IA\b", address)
        city = city_match.group(1) if city_match else ""

        email = x('//a[contains(@href,"mailto:")]/text()')
        website = x('//a[contains(@href,"http") and contains(text(),"Website")]/@href')

        item = {
            "profile_url": profile_url,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "image_url": image_url,
            "office_name": office_name,
            "address": address,
            "zipcode": zipcode,
            "description": description,
            "languages": languages,
            "social": social_links,
            "website": website,
            "email": email,
            "title": title,
            "country": country,
            "state": state,
            "city": city,
            "agent_phone_numbers": agent_phone_numbers,
            "office_phone_numbers": [],
        }

        AgentItem.objects(profile_url=profile_url).update_one(
            upsert=True,
            **{f"set__{k}": v for k, v in item.items()}
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    Parser().start()
