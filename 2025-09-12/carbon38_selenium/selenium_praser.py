import re
import time
import psutil
import logging
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


# Configurations
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "carbon38_selenium"
URL_COLLECTION = "product_urls"
DETAILS_COLLECTION = "product_details"

# MongoDB 
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
urls_collection = db[URL_COLLECTION]
details_collection = db[DETAILS_COLLECTION]


class Carbon38Parser:
    """Parser to extract product details from Carbon38 product pages"""

    def __init__(self):

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("Carbon38Parser")

        # Selenium
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 30)

    def safe_get(self, url: str, timeout: int = 60):
        """Safely load a URL with timeout handling"""
        self.driver.set_page_load_timeout(timeout)
        try:
            self.driver.get(url)
        except TimeoutException:
            self.logger.warning(f"Timeout loading {url}, forcing stop...")
            self.driver.execute_script("window.stop();")

    def parse_product_page(self, url: str):
        """Extract product details from a single product page"""
        self.safe_get(url)

        try:
            product_name = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//h1[contains(@class,"ProductMeta__Title")]'))
            ).text.strip()

            brand = self.driver.find_element(By.XPATH, '//h2[contains(@class,"ProductMeta__Vendor")]//a').text.strip()
            price = self.driver.find_element(By.XPATH, '//span[contains(@class,"ProductMeta__Price")]').text.strip()
            colour = self.driver.find_element(By.XPATH, '//span[contains(@class,"ProductForm__SelectedValue")]').text.strip()

            size_elements = self.driver.find_elements(By.XPATH, '//input[contains(@class,"SizeSwatch__Radio")]')
            sizes = [el.get_attribute("value").strip() for el in size_elements if el.get_attribute("value")]

            image_elements = self.driver.find_elements(By.XPATH, '//img[contains(@class,"Product__SlideImage")]')
            images = []
            for el in image_elements:
                src = el.get_attribute("src")
                if src:
                    images.append(src if src.startswith("http") else "https:" + src)

            description = ""
            try:
                faq_element = self.driver.find_element(By.XPATH, '//div[contains(@class,"Faq__AnswerWrapper")]//p')
                raw_html = faq_element.get_attribute("innerHTML")
                description = re.sub(r'<br\s*/?>', '\n', raw_html)
                description = re.sub(r'<[^>]+>', '', description).strip()
            except NoSuchElementException:
                pass

            return {
                "product_url": url,
                "product_name": product_name,
                "brand": brand,
                "price": price,
                "colour": colour,
                "sizes": sizes,
                "images": images,
                "description": description,
            }

        except Exception as e:
            self.logger.error(f"Error parsing {url}: {e}")
            return None

    def run(self):
        """Main loop to parse all product URLs from MongoDB"""
        urls = urls_collection.find({}, {"url": 1, "_id": 0})
        parsed_count = 0

        for entry in urls:
            url = entry["url"]
            details = self.parse_product_page(url)

            if details:
                details_collection.update_one(
                    {"product_url": details["product_url"]},
                    {"$set": details},
                    upsert=True
                )
                parsed_count += 1

            time.sleep(2)

        self.driver.quit()
        client.close()
        return parsed_count


if __name__ == "__main__":
    start_time = time.time()
    process = psutil.Process()

    parser = Carbon38Parser()
    total_parsed = parser.run()

    elapsed_time = time.time() - start_time
    mem_usage = process.memory_info().rss / (1024 * 1024)  

    print(f"\n[Efficiency Report]")
    print(f"Parsed Products: {total_parsed}")
    print(f"Execution Time: {elapsed_time:.2f} seconds")
    print(f"Memory Usage: {mem_usage:.2f} MB")
