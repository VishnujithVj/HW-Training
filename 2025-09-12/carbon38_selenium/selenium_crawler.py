import time
from urllib.parse import urljoin
from pymongo import MongoClient, errors
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging


# Configurations
START_URL = "https://carbon38.com/en-in/collections/tops?filter.p.m.custom.available_or_waitlist=1"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "carbon38_selenium"
COLLECTION_NAME = "product_urls"

# XPaths
PRODUCT_LINK_XPATH = "//a[@class='ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage']"
NEXT_BUTTON_XPATH = "//a[@class='Pagination__NavItem Link Link--primary' and @title='Next page']"


class Carbon38Crawler:
    def __init__(self):
        # ✅ Logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("Carbon38Crawler")

        # ✅ Mongo
        client = MongoClient(MONGO_URI)
        self.db = client[DB_NAME]
        self.col = self.db[COLLECTION_NAME]
        self.col.create_index("url", unique=True)

        # ✅ Selenium
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--headless=new")  # Uncomment for headless mode

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 60)

    def safe_get(self, url, timeout=60):
        """Load a page with timeout, stop if it takes too long"""
        self.driver.set_page_load_timeout(timeout)
        try:
            self.driver.get(url)
        except TimeoutException:
            self.logger.warning(f"Timeout loading {url}, stopping load...")
            self.driver.execute_script("window.stop();")

    def run(self, start_url=START_URL):
        url = start_url
        while url:
            self.logger.info(f"Visiting page: {url}")
            self.safe_get(url)

            try:
                self.wait.until(EC.presence_of_all_elements_located((By.XPATH, PRODUCT_LINK_XPATH)))
            except TimeoutException:
                self.logger.error(f"No products loaded on {url}")
                break

            product_elements = self.driver.find_elements(By.XPATH, PRODUCT_LINK_XPATH)
            self.logger.info(f"Found {len(product_elements)} products on this page")

            for el in product_elements:
                href = el.get_attribute("href")
                if not href:
                    continue
                full_url = urljoin("https://carbon38.com", href)
                try:
                    self.col.insert_one({"url": full_url})
                    self.logger.info(f"Inserted {full_url}")
                except errors.DuplicateKeyError:
                    self.logger.debug(f"Skipping duplicate {full_url}")
                except Exception as e:
                    self.logger.error(f"Mongo insert error for {full_url}: {e}")

            # ✅ Pagination
            try:
                next_button = self.driver.find_element(By.XPATH, NEXT_BUTTON_XPATH)
                next_page = next_button.get_attribute("href")
                if next_page:
                    url = urljoin("https://carbon38.com", next_page)
                    continue
            except NoSuchElementException:
                self.logger.info("No more pages. Exiting.")
                break

        self.driver.quit()


if __name__ == "__main__":
    crawler = Carbon38Crawler()
    crawler.run()
