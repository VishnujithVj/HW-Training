import asyncio
from playwright.async_api import async_playwright
from pymongo import MongoClient, errors
from urllib.parse import urljoin

# Configurations
START_URL = "https://carbon38.com/en-in/collections/tops?filter.p.m.custom.available_or_waitlist=1"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "carbon38_playwright"
COLLECTION_NAME = "product_urls"

# Your XPaths
PRODUCT_LINK_XPATH = "//a[@class='ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage']"
NEXT_BUTTON_XPATH = "//a[@class='Pagination__NavItem Link Link--primary' and @title='Next page']"

async def scrape():
    # Initialize Mongo
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]
    col.create_index("url", unique=True)

    async with async_playwright() as p:
        # Stealth-like settings
        browser = await p.chromium.launch(
            headless=False,  # change to True for production
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
            print(f"Visiting page: {url}")
            try:
                await page.goto(url, timeout=90000, wait_until="commit")
                await page.wait_for_selector(PRODUCT_LINK_XPATH, timeout=60000)
            except Exception as e:
                print(f"Failed to load {url}: {e}")
                break

            # Extract product URLs
            product_links = await page.locator(PRODUCT_LINK_XPATH).evaluate_all(
                "elements => elements.map(el => el.getAttribute('href'))"
            )

            for href in product_links:
                if not href:
                    continue
                full_url = urljoin("https://carbon38.com", href)
                try:
                    col.insert_one({"url": full_url})
                    print(f"Inserted {full_url}")
                except errors.DuplicateKeyError:
                    print(f"Skipping duplicate {full_url}")
                except Exception as e:
                    print(f"Mongo insert error for {full_url}: {e}")

            # ✅ FIXED: safely check if "Next page" exists
            next_button = await page.locator(NEXT_BUTTON_XPATH).element_handle(timeout=2000)
            if next_button:
                next_page = await next_button.get_attribute("href")
                if next_page:
                    url = urljoin("https://carbon38.com", next_page)
                    continue
            print("No more pages. Exiting.")
            break

        await browser.close()
    client.close()

if __name__ == "__main__":
    asyncio.run(scrape())
