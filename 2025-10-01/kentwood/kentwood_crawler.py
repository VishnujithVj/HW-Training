import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from pymongo import MongoClient

# Config
URL = "https://www.kentwood.com/roster/agents"
JSON_FILE = Path("agents_urls.json")
LOG_FILE = Path("crawler.log")

DB_NAME = "kentwood_db"
COLLECTION_NAME = "agents_urls"

SCROLL_PAUSE = 0.5
MAX_IDLE_ROUNDS = 5
INITIAL_WAIT = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, mode="a")]
)
logger = logging.getLogger("kentwood_crawler")

client = MongoClient("mongodb://localhost:27017/")
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def save_json_line(url_data: dict):
    """Append a single URL entry to JSON file."""
    with JSON_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(url_data) + "\n")

def save_to_mongo(url_data: dict):
    """Save URL data to MongoDB if not exists."""
    collection.update_one({"url": url_data["url"]}, {"$set": url_data}, upsert=True)

def extract_agent_urls(driver) -> List[str]:
    """Extract agent URLs with primary and fallback selectors."""
    urls = set()
    try:
        elems = driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-outline-primary.button.hollow[href^='/bio/']")
        for el in elems:
            href = el.get_attribute("href")
            if href:
                urls.add(href)
    except WebDriverException:
        logger.debug("Primary selector failed")

    try:
        elems2 = driver.find_elements(By.CSS_SELECTOR, "a[href*='/bio/']")
        for el in elems2:
            href = el.get_attribute("href")
            if href:
                urls.add(href)
    except WebDriverException:
        logger.debug("Fallback selector failed")
    return list(urls)


def crawl_kentwood():
    seen = set()
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    
    driver = uc.Chrome(options=options, version_main=139)
    try:
        logger.info(f"Opening roster page: {URL}")
        driver.get(URL)
        time.sleep(INITIAL_WAIT)

        idle_rounds = 0
        last_count = 0

        while idle_rounds < MAX_IDLE_ROUNDS:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)

            urls = extract_agent_urls(driver)
            new_urls = [u for u in urls if u not in seen]

            if new_urls:
                logger.info(f"Found {len(new_urls)} new agents")
                for url in new_urls:
                    url_data = {
                        "url": url,
                        "scraped_ts": datetime.utcnow().isoformat(),
                    }
                    try:
                        save_json_line(url_data)
                        save_to_mongo(url_data)
                        logger.info(f"Saved URL: {url}")
                        seen.add(url)
                    except Exception as e:
                        logger.error(f"Error saving {url}: {e}")
                idle_rounds = 0
            else:
                idle_rounds += 1
                logger.info(f"No new agents, idle_rounds={idle_rounds}/{MAX_IDLE_ROUNDS}")

            if len(urls) == last_count:
                idle_rounds += 1
            last_count = len(urls)

        logger.info(f"Finished. Total agents collected: {len(seen)}")

    except Exception as e:
        logger.exception(f"Crawl error: {e}")
    finally:
        driver.quit()

# Main
if __name__ == "__main__":
    crawl_kentwood()
