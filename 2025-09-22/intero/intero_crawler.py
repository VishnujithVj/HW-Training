import time
import json
import logging
from pathlib import Path
from typing import List

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, JavascriptException
from pymongo import MongoClient

# CONFIG
INTERO_ROSTER_URL = "https://www.intero.com/roster/agents"
JSON_PATH = Path("agents_urls.json")
LOG_PATH = Path("crawler.log")
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "intero_db"
MONGO_COLLECTION = "agents_urls"

SCROLL_INCREMENT = 500
SCROLL_PAUSE = 0.4
MAX_IDLE_ROUNDS = 5      
INITIAL_WAIT = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("intero_crawler")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]


def save_json_line(url: str):
    """Append a single JSON line per URL to file."""
    with JSON_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"url": url}) + "\n")


def save_to_mongo(url: str):
    """Insert URL into MongoDB if not present."""
    if not collection.find_one({"url": url}):
        collection.insert_one({"url": url})


def extract_agent_urls(driver) -> List[str]:
    urls = set()

    try:
        elems = driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-outline-primary.button.hollow")
        for el in elems:
            href = el.get_attribute("href")
            if href:
                urls.add(href)
    except WebDriverException:
        logger.debug("Primary selector failed or empty")

    try:
        elems2 = driver.find_elements(By.CSS_SELECTOR, "a[href*='/bio/']")
        for el in elems2:
            href = el.get_attribute("href")
            if href:
                urls.add(href)
    except WebDriverException:
        logger.debug("Fallback selector failed or empty")

    return list(urls)


def crawl_intero():
    seen = set()

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = None
    try:
        driver = uc.Chrome(options=options, version_main=139)
        logger.info(f"Opening roster page: {INTERO_ROSTER_URL}")
        driver.get(INTERO_ROSTER_URL)

        logger.info(f"Waiting {INITIAL_WAIT}s for initial load")
        time.sleep(INITIAL_WAIT)

        idle_rounds = 0
        last_seen_count = 0

        while idle_rounds < MAX_IDLE_ROUNDS:

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE * 5)

            urls = extract_agent_urls(driver)
            new_urls = [u for u in urls if u not in seen]

            if new_urls:
                logger.info(f"Found {len(new_urls)} new agents")
                for url in new_urls:
                    try:
                        save_json_line(url)
                        save_to_mongo(url)
                        logger.info(f"Saved {url}")
                        seen.add(url)
                    except Exception as e:
                        logger.error(f"Error saving {url}: {e}")
                idle_rounds = 0
            else:
                idle_rounds += 1
                logger.info(f"No new agents, idle_rounds={idle_rounds}/{MAX_IDLE_ROUNDS}")

            if len(urls) == last_seen_count:
                idle_rounds += 1
            last_seen_count = len(urls)

        logger.info(f"Finished. Total agents collected: {len(seen)}")

    except Exception as e:
        logger.exception(f"Crawl error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    crawl_intero()
