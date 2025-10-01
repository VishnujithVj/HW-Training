import time
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from pymongo import MongoClient
from bs4 import BeautifulSoup

# Config
JSON_FILE = Path("agents_details.json")
LOG_FILE = Path("parser.log")

DB_NAME = "kentwood_db"
URL_COLLECTION = "agents_urls"
DETAILS_COLLECTION = "agents_details"

WAIT_TIME = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, mode="a")]
)
logger = logging.getLogger("kentwood_parser")

client = MongoClient("mongodb://localhost:27017/")
db = client[DB_NAME]
url_collection = db[URL_COLLECTION]
details_collection = db[DETAILS_COLLECTION]


def save_json_line(data: Dict):
    with JSON_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

def save_to_mongo(data: Dict):
    details_collection.update_one({"profile_url": data["profile_url"]}, {"$set": data}, upsert=True)

def safe_find_text(driver, xpath: str) -> str:
    try:
        el = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return el.text.strip()
    except TimeoutException:
        return ""

def safe_find_attr(driver, xpath: str, attr: str) -> str:
    try:
        el = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return el.get_attribute(attr) or ""
    except TimeoutException:
        return ""

def safe_find_multiple_texts(driver, xpath: str) -> List[str]:
    try:
        elems = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        return [el.text.strip() for el in elems if el.text.strip()]
    except TimeoutException:
        return []

def parse_address(address_html: str) -> Dict:
    """Extract street, city, state, zipcode"""
    soup = BeautifulSoup(address_html, "html.parser")
    text = soup.get_text(separator=" ").strip()
    street = city = state = zipcode = ""
    match = re.search(r"^(.*?)([A-Za-z\s]+)\s+([A-Z]{2})\s+(\d{5})$", text)
    if match:
        street, city, state, zipcode = match.groups()
    return {
        "address": street.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "zipcode": zipcode.strip(),
        "country": "USA"
    }

def parse_social_links(driver) -> List[str]:
    links = []
    try:
        elems = driver.find_elements(By.XPATH, "//ul[contains(@class,'social-icons')]/li/a")
        for el in elems:
            href = el.get_attribute("href")
            if href:
                links.append(href.strip())
    except WebDriverException:
        pass
    return links

def parse_website(driver) -> str:
    return safe_find_attr(driver, "//li[contains(@class,'agent-website')]/a", "href")

def parse_email(driver) -> str:
    href = safe_find_attr(driver, "//li[contains(@class,'agent-email')]/a", "href")
    return href.replace("mailto:", "").strip() if href else ""

def parse_phone_numbers(driver, xpath: str) -> List[str]:
    return safe_find_multiple_texts(driver, xpath)


class KentwoodParser:
    def __init__(self):
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = uc.Chrome(options=options, version_main=139)

    def parse_agent(self, url: str) -> Dict:
        self.driver.get(url)
        time.sleep(2)

        first_name = middle_name = last_name = ""
        try:
            p_elem = self.driver.find_element(By.XPATH, "//p[@class='rng-agent-profile-contact-name']")
            full_name = p_elem.get_attribute("innerText").split("\n")[0].strip()
            if full_name:
                parts = full_name.split()
                first_name = parts[0]
                if len(parts) == 2:
                    last_name = parts[1]
                elif len(parts) > 2:
                    middle_name = " ".join(parts[1:-1])
                    last_name = parts[-1]
        except:
            pass

    
        desc_html = safe_find_attr(self.driver, "//div[contains(@id,'widget-text')]", "innerHTML")
        description = BeautifulSoup(desc_html, "html.parser").get_text(separator=" ").strip() if desc_html else ""


        address_html = safe_find_attr(self.driver, "//li[contains(@class,'rng-agent-profile-contact-address')]", "innerHTML")
        addr_data = parse_address(address_html) if address_html else {"address":"","city":"","state":"","zipcode":"","country":"USA"}

    
        data = {
            "profile_url": url,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "image_url": safe_find_attr(self.driver, "//img[contains(@class,'rng-agent-profile-photo')]", "src"),
            "office_name": safe_find_text(self.driver, "//div[contains(@class,'office-name')]"),
            "address": addr_data["address"],
            "city": addr_data["city"],
            "state": addr_data["state"],
            "zipcode": addr_data["zipcode"],
            "country": addr_data["country"],
            "description": description,
            "languages": safe_find_multiple_texts(self.driver, "//div[contains(@class,'languages')]//li"),
            "social": [el.get_attribute("href") for el in self.driver.find_elements(By.XPATH, "//li[contains(@class,'social-')]/a") if el.get_attribute("href")],
            "website": safe_find_attr(self.driver, "//li[@class='rng-agent-profile-contact-website']/a", "href"),
            "email": (lambda e: e.replace("mailto:", "").strip() if e and e.startswith("mailto:") else e)(
                safe_find_attr(self.driver, "//li[@class='rng-agent-profile-contact-email']/a", "href")
            ),
            "title": safe_find_text(self.driver, "//span[@class='rng-agent-profile-contact-title']"),
            "agent_phone_numbers": parse_phone_numbers(self.driver, "//li[@class='rng-agent-profile-contact-phone']/a"),
            "office_phone_numbers": parse_phone_numbers(self.driver, "//li[@class='rng-agent-office-contact-phone']/a"),
            "scraped_ts": datetime.utcnow().isoformat()
        }
        return data

    def crawl_agents(self):
        urls = [doc["url"] for doc in url_collection.find()]
        logger.info(f"Found {len(urls)} agent URLs in DB")

        for idx, url in enumerate(urls, start=1):
            try:
                logger.info(f"[{idx}/{len(urls)}] Parsing agent: {url}")
                agent_data = self.parse_agent(url)
                save_to_mongo(agent_data)
                save_json_line(agent_data)
                logger.info(f"Saved agent data for {url}")
            except Exception as e:
                logger.error(f"Error parsing {url}: {e}")

    def close(self):
        self.driver.quit()

# Main
if __name__ == "__main__":
    parser = KentwoodParser()
    try:
        parser.crawl_agents()
    finally:
        parser.close()
