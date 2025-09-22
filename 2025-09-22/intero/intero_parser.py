#!/usr/bin/env python3
"""
Intero Agents Details Parser (XPath version)
- Loads agent profile URLs from MongoDB (intero_db.agents_urls)
- Visits each agent profile page
- Extracts agent details with XPath
- Saves incrementally to:
    * MongoDB (intero_db.agents_details)
    * agents_details.json (one JSON object per line)
    * parser.log (logging)
"""

import time
import re
import json
import logging
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from pymongo import MongoClient

# ---------------- CONFIG ----------------
JSON_PATH = Path("agents_details.json")
LOG_PATH = Path("parser.log")
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "intero_db"
URLS_COLLECTION = "agents_urls"
DETAILS_COLLECTION = "agents_details"

INITIAL_WAIT = 3

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("intero_agents_details")

# ---------------- PERSISTENCE ----------------
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
urls_collection = db[URLS_COLLECTION]
details_collection = db[DETAILS_COLLECTION]


def save_json_line(data: dict):
    """Append one JSON object per line to agents_details.json."""
    with JSON_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def save_to_mongo(data: dict):
    """Insert agent details into MongoDB if not present (dedupe by profile_url)."""
    if not details_collection.find_one({"profile_url": data["profile_url"]}):
        details_collection.insert_one(data)


# ---------------- SCRAPER ----------------
def parse_agent_page(driver, url: str) -> dict:
    """Extract structured agent details from profile page using XPath."""
    driver.get(url)
    time.sleep(INITIAL_WAIT)

    def safe_xpath(xpath, attr=None, multi=False):
        """Helper to safely extract text/attribute(s) via XPath."""
        try:
            if multi:
                els = driver.find_elements(By.XPATH, xpath)
                return [el.get_attribute(attr) if attr else el.text.strip()
                        for el in els if el]
            el = driver.find_element(By.XPATH, xpath)
            return el.get_attribute(attr) if attr else el.text.strip()
        except (WebDriverException, NoSuchElementException):
            return [] if multi else ""

    # ---------------- Extract raw fields ----------------
    name_block = safe_xpath("//p[contains(@class,'rng-agent-profile-contact-name')]")
    title = safe_xpath("//span[contains(@class,'rng-agent-profile-contact-title')]")
    image_url = safe_xpath("//img[contains(@class,'rng-agent-profile-photo')]", "src")
    office_name = safe_xpath("//div[contains(@class,'rng-agent-profile-contact-office')]")
    address_block = safe_xpath("//li[contains(@class,'rng-agent-profile-contact-address')]")
    description = safe_xpath("//div[starts-with(@id,'body-text')]")
    website = safe_xpath("//li[contains(@class,'rng-agent-profile-contact-website')]/a", "href")
    email = safe_xpath("//li[contains(@class,'rng-agent-profile-contact-email')]/a", "href")
    social_links = safe_xpath("//div[contains(@class,'rng-agent-profile-contact-social')]//a", "href", multi=True)
    agent_phones = safe_xpath("//li[contains(@class,'rng-agent-profile-contact-phone')]/a", "href", multi=True)
    office_phones = safe_xpath("//li[contains(@class,'rng-agent-profile-contact-office-phone')]/a", "href", multi=True)

    # ---------------- Parse name ----------------
    first_name, middle_name, last_name = "", "", ""
    if name_block:
        parts = name_block.split()

        # Remove the title (Realtor, Broker, etc.) if it appears inside name block
        if title and title in parts:
            parts = [p for p in parts if p != title]

        if len(parts) == 1:
            first_name = parts[0]
        elif len(parts) == 2:
            first_name, last_name = parts
        elif len(parts) > 2:
            first_name = parts[0]
            middle_name = " ".join(parts[1:-1])
            last_name = parts[-1]

    # ---------------- Parse email ----------------
    if email and email.startswith("mailto:"):
        email = email.replace("mailto:", "")

    # ---------------- Parse address ----------------
    street, city, state, zipcode, country = "", "", "", "", "USA"
    if address_block:
        # Example: 32145 Alvarado-Niles Road Suite 101 Union City CA 94587
        match = re.match(r"^(.*)\s+([\w\s]+)\s+([A-Z]{2})\s+(\d{5})$", address_block.strip())
        if match:
            street, city, state, zipcode = match.groups()
        else:
            street = address_block.strip()

    # ---------------- Normalize phones ----------------
    def normalize_phones(phone_list):
        nums = []
        for ph in phone_list:
            if ph and ph.startswith("tel:"):
                nums.append(ph.replace("tel:", ""))
        return nums

    agent_phone_numbers = normalize_phones(agent_phones)
    office_phone_numbers = normalize_phones(office_phones)

    # ---------------- Final structured dict ----------------
    return {
        "profile_url": url,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "image_url": image_url,
        "office_name": office_name,
        "address": street,
        "description": description,
        "languages": [],  # not present in markup
        "social": social_links,
        "website": website,
        "email": email,
        "title": title,
        "country": country,
        "city": city,
        "zipcode": zipcode,
        "state": state,
        "agent_phone_numbers": agent_phone_numbers,
        "office_phone_numbers": office_phone_numbers,
    }


# ---------------- MAIN ----------------
def crawl_agent_details():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = None
    try:
        driver = uc.Chrome(options=options, version_main=139)

        urls = list(urls_collection.find({}))
        total = len(urls)

        for idx, doc in enumerate(urls, start=1):
            url = doc["url"]

            if details_collection.find_one({"profile_url": url}):
                logger.info(f"[{idx}/{total}] Skipping {url}, already scraped")
                continue

            try:
                logger.info(f"[{idx}/{total}] Scraping {url}")
                details = parse_agent_page(driver, url)

                # Save one by one
                save_json_line(details)
                save_to_mongo(details)

                logger.info(f"[{idx}/{total}] ✅ Saved details for {url}")
            except Exception as e:
                logger.error(f"[{idx}/{total}] ❌ Error scraping {url}: {e}")

    except Exception as e:
        logger.exception(f"🔥 Fatal error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    crawl_agent_details()
