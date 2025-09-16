import asyncio
import re
import time
import psutil
import logging
from datetime import datetime
from pymongo import MongoClient, errors
from playwright.async_api import async_playwright

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "carbon38_playwright"
URL_COLLECTION = "product_urls"
DETAILS_COLLECTION = "product_details"

CONCURRENCY_LIMIT = 5  

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("parser.log"), logging.StreamHandler()]
)

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
urls_collection = db[URL_COLLECTION]
details_collection = db[DETAILS_COLLECTION]


async def safe_text(page, selector: str, timeout: int = 5000) -> str | None:
    """Safely extract inner text from a selector or return None if missing."""
    try:
        el = await page.wait_for_selector(selector, timeout=timeout)
        return (await el.inner_text()).strip()
    except Exception:
        return None


async def extract_product_details(page, url: str) -> dict | None:
    """Extract structured product details from a Carbon38 product page."""
    try:
        response = await page.goto(url, timeout=90000, wait_until="domcontentloaded")
        status_code = response.status if response else None
        logging.info(f"Visiting: {url} | Status: {status_code}")
    except Exception as e:
        logging.error(f"Failed to load {url}: {e}")
        return None

    try:
        product_name = await safe_text(page, '//h1[contains(@class,"ProductMeta__Title")]')
        brand = await safe_text(page, '//h2[contains(@class,"ProductMeta__Vendor")]//a')
        price = await safe_text(page, '//span[contains(@class,"ProductMeta__Price")]')
        colour = await safe_text(page, '//span[contains(@class,"ProductForm__SelectedValue")]')

        sizes = await page.eval_on_selector_all(
            '//input[contains(@class,"SizeSwatch__Radio")]',
            "els => els.map(el => el.getAttribute('value')).filter(Boolean)"
        )

        images = await page.eval_on_selector_all(
            '//img[contains(@class,"Product__SlideImage")]',
            "els => els.map(el => el.getAttribute('src')).filter(Boolean)"
        )
        images = [img if img.startswith("http") else "https:" + img for img in images]

        faq_elements = await page.query_selector_all('//div[contains(@class,"Faq__AnswerWrapper")]//p')
        descriptions = []
        for el in faq_elements:
            raw_html = await el.inner_html()
            text = re.sub(r'<br\s*/?>', '\n', raw_html)
            text = re.sub(r'<[^>]+>', '', text).strip()
            if text:
                descriptions.append(text)
        description = "\n\n".join(descriptions)

        return {
            "product_url": url,
            "product_name": product_name,
            "brand": brand,
            "price": price,
            "colour": colour,
            "sizes": sizes or [],
            "images": images,
            "description": description,
            "last_updated": datetime.utcnow(),
        }

    except Exception as e:
        logging.error(f"Error parsing {url}: {e}")
        return None


async def extract_with_retry(page, url: str, retries: int = 3) -> dict | None:
    """Retry product detail extraction in case of errors/timeouts."""
    for attempt in range(1, retries + 1):
        details = await extract_product_details(page, url)
        if details:
            return details
        logging.warning(f"Retrying {url} (attempt {attempt}/{retries})...")
        await asyncio.sleep(3)
    return None


async def scrape_products():
    urls = [doc["url"] for doc in urls_collection.find({}, {"url": 1, "_id": 0})]
    scraped_count = 0
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115 Safari/537.36"
            )
        )

        await context.route(
            "**/*",
            lambda route: (
                route.abort()
                if route.request.resource_type in ["font", "stylesheet"]
                else route.continue_()
            ),
        )

        async def process_url(url: str) -> int:
            async with semaphore:
                page = await context.new_page()
                details = await extract_with_retry(page, url)
                if details:
                    try:
                        details_collection.update_one(
                            {"product_url": details["product_url"]},
                            {"$set": details},
                            upsert=True
                        )
                        logging.info(f"Saved: {url}")
                        await page.close()
                        return 1
                    except errors.PyMongoError as e:
                        logging.error(f"MongoDB insert error for {url}: {e}")
                await page.close()
                return 0

        results = await asyncio.gather(*(process_url(url) for url in urls))
        scraped_count = sum(results)

        await context.close()
        await browser.close()

    return scraped_count


def log_efficiency(start_time: float):
    elapsed_time = time.time() - start_time
    process = psutil.Process()
    mem_usage = process.memory_info().rss / (1024 * 1024)
    logging.info(f"Execution time: {elapsed_time:.2f} seconds")
    logging.info(f"Memory usage: {mem_usage:.2f} MB")


if __name__ == "__main__":
    start_time = time.time()
    count = asyncio.run(scrape_products())
    client.close()
    logging.info(f"Finished scraping {count} products.")
    log_efficiency(start_time)
