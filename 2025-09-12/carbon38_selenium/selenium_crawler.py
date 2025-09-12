from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
import time

# --- Configurations ---
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "carbon38"
MONGO_COLLECTION = "product_urls"
START_URL = "https://carbon38.com/en-in/collections/tops?filter.p.m.custom.available_or_waitlist=1"
WAIT_TIME = 20  # Increased wait time for slow-loading pages

# --- Setup MongoDB ---
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

# --- Setup Selenium ---
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")  # headless mode
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Auto-download matching ChromeDriver and increase start timeout
service = Service(ChromeDriverManager().install(), start_timeout=300)
driver = webdriver.Chrome(service=service, options=options)
driver.get(START_URL)
wait = WebDriverWait(driver, WAIT_TIME)

def extract_product_links():
    """Extract product links on the current page."""
    links = []
    try:
        wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//a[contains(@class,'ProductItem__ImageWrapper')]")
        ))
    except TimeoutException:
        print("Timed out waiting for product links on this page")
        return links

    anchors = driver.find_elements(By.XPATH, "//a[contains(@class,'ProductItem__ImageWrapper')]")
    for a in anchors:
        href = a.get_attribute("href")
        if href:
            links.append(href.strip())

    # Deduplicate
    return list(set(links))


def go_to_next_page():
    """Click or navigate to the next pagination page. Returns True if successful."""
    try:
        next_page = driver.find_element(By.XPATH, "//a[@title='Next page']")
        next_href = next_page.get_attribute("href")
        if next_href:
            driver.get(next_href)
        else:
            next_page.click()
        return True
    except NoSuchElementException:
        return False
    except Exception as e:
        print(f"Error going to next page: {e}")
        return False


def save_links(links):
    """Save links into MongoDB with upsert to avoid duplicates."""
    for url in links:
        collection.update_one({"url": url}, {"$set": {"url": url}}, upsert=True)


def main():
    page_count = 1
    while True:
        print(f"Scraping page {page_count}: {driver.current_url}")
        links = extract_product_links()
        print(f" Found {len(links)} product links")
        save_links(links)

        if not go_to_next_page():
            print("No more pages. Exiting.")
            break

        time.sleep(2)  # wait a bit for next page to load
        page_count += 1

    driver.quit()
    client.close()


if __name__ == "__main__":
    main()
