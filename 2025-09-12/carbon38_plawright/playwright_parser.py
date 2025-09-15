import asyncio
import re
from playwright.async_api import async_playwright
from pymongo import MongoClient
from w3lib.html import remove_tags


# --- Configurations ---
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "carbon38_playwright"
URL_COLLECTION = "product_urls"        # input URLs
DETAILS_COLLECTION = "product_details" # output details


# --- MongoDB Setup ---
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
urls_collection = db[URL_COLLECTION]
details_collection = db[DETAILS_COLLECTION]


async def parse_product_page(page, url):
    """Extract product details from a single product page using XPath."""
    try:
        await page.goto(
            url,
            timeout=90000,
            wait_until="domcontentloaded"
        )
    except Exception as e:
        print(f"❌ Failed to load {url}: {e}")
        return None

    try:
        # --- Product name ---
        product_name = await page.locator(
            '//h1[contains(@class,"ProductMeta__Title")]'
        ).inner_text(timeout=10000)

        # --- Brand ---
        brand = await page.locator(
            '//h2[contains(@class,"ProductMeta__Vendor")]//a'
        ).inner_text(timeout=10000)

        # --- Price ---
        price = await page.locator(
            '//span[contains(@class,"ProductMeta__Price")]'
        ).inner_text(timeout=10000)

        # --- Colour ---
        colour = await page.locator(
            '//span[contains(@class,"ProductForm__SelectedValue")]'
        ).inner_text(timeout=10000)

        # --- Sizes (list) ---
        sizes = await page.eval_on_selector_all(
            '//input[contains(@class,"SizeSwatch__Radio")]',
            "els => els.map(el => el.getAttribute('value')).filter(Boolean)"
        )

        # --- Images (gallery) ---
        images = await page.eval_on_selector_all(
            '//img[contains(@class,"Product__SlideImage")]',
            "els => els.map(el => el.getAttribute('src')).filter(Boolean)"
        )
        images = [img if img.startswith("http") else "https:" + img for img in images]

        # --- FAQ Section (Editor Notes / Descriptions) ---
        faq_elements = await page.query_selector_all(
            '//div[contains(@class,"Faq__AnswerWrapper")]//p'
        )
        description = ""
        if faq_elements:
            raw_html = await faq_elements[0].inner_html()
            description = re.sub(r'<br\s*/?>', '\n', raw_html)
            description = re.sub(r'<[^>]+>', '', description).strip()

        details = {
            "product_url": url,
            "product_name": product_name.strip(),
            "brand": brand.strip(),
            "price": price.strip(),
            "colour": colour.strip(),
            "sizes": [s.strip() for s in sizes],
            "images": images,
            "description": description,
        }

        return details

    except Exception as e:
        print(f"⚠️ Error parsing {url}: {e}")
        return None


async def main():
    urls = urls_collection.find({}, {"url": 1, "_id": 0})
    count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115 Safari/537.36"
            )
        )

        # Block unnecessary resources (images, fonts, stylesheets)
        await context.route(
            "**/*",
            lambda route: (
                route.abort()
                if route.request.resource_type in ["font", "stylesheet"]
                else route.continue_()
            ),
        )

        page = await context.new_page()

        for entry in urls:
            url = entry["url"]
            print(f"🔎 Scraping product: {url}")
            details = await parse_product_page(page, url)

            if details:
                details_collection.update_one(
                    {"product_url": details["product_url"]},
                    {"$set": details},
                    upsert=True
                )
                count += 1
                print(f" ✅ Saved product: {details['product_name']}")

            await asyncio.sleep(2)  # polite delay

        await browser.close()

    print(f"\n🎉 Finished scraping {count} products.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
