import asyncio
import logging
import time
import psutil
from pymongo import MongoClient, errors
from urllib.parse import urljoin
from playwright.async_api import async_playwright

# Configurations 
START_URL = "https://carbon38.com/en-in/collections/tops?filter.p.m.custom.available_or_waitlist=1"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "carbon38_playwright"
COLLECTION_NAME = "product_urls"

PRODUCT_LINK_XPATH = "//a[@class='ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage']"
NEXT_BUTTON_XPATH = "//a[@class='Pagination__NavItem Link Link--primary' and @title='Next page']"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("crawler.log"), logging.StreamHandler()]
)


async def scrape_product_urls():
    """Scrape product URLs from Carbon38 and store in MongoDB."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]
    col.create_index("url", unique=True)

    async with async_playwright() as p:  
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768}
        )
        page = await context.new_page()

        url = START_URL
        while url:
            try:
                response = await page.goto(url, timeout=90000, wait_until="commit")
                status_code = response.status if response else None
                logging.info(f"Visiting: {url} | Status: {status_code}")

                await page.wait_for_selector(PRODUCT_LINK_XPATH, timeout=60000)
            except Exception as e:
                logging.error(f"Failed to load {url}: {e}")
                break

            
            product_links = await page.locator(PRODUCT_LINK_XPATH).evaluate_all(
                "elements => elements.map(el => el.getAttribute('href'))"
            )

            for href in product_links:
                if not href:
                    continue
                full_url = urljoin("https://carbon38.com", href)
                try:
                    col.insert_one({"url": full_url})
                    logging.info(f"Inserted: {full_url}")
                except errors.DuplicateKeyError:
                    logging.debug(f"Duplicate skipped: {full_url}")
                except Exception as e:
                    logging.error(f"Mongo insert error for {full_url}: {e}")

        
            try:
                next_button = await page.locator(NEXT_BUTTON_XPATH).element_handle(timeout=2000)
                if next_button:
                    next_page = await next_button.get_attribute("href")
                    if next_page:
                        url = urljoin("https://carbon38.com", next_page)
                        continue
            except Exception:
                pass

            logging.info("No more pages found. Stopping.")
            break

        await browser.close()
    client.close()


def log_efficiency(start_time):
    """Log memory and time usage."""
    elapsed_time = time.time() - start_time
    process = psutil.Process()
    mem_info = process.memory_info().rss / (1024 * 1024)
    logging.info(f"Execution time: {elapsed_time:.2f} seconds")
    logging.info(f"Memory usage: {mem_info:.2f} MB")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(scrape_product_urls())
    log_efficiency(start_time)
