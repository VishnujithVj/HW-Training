import asyncio
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from pymongo import MongoClient


class BillaCrawler:
    def __init__(self, start_url, mongo_uri="mongodb://localhost:27017", db_name="billa_site_db"):
        self.start_url = start_url
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.product_urls_col = self.db["product_urls"]

        # logging
        log_path = Path("crawler.log")
        logging.basicConfig(
            filename=log_path,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )
        self.logger = logging.getLogger("BillaCrawler")

    async def run(self):
        """Main entry point"""
        self.logger.info("Starting Billa crawler...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(user_agent="Mozilla/5.0 (compatible; BillaCrawler/1.0)")
            page = await context.new_page()

            categories = await self.get_categories(page)

            for name, url in categories.items():
                self.logger.info(f"Scraping category: {name} -> {url}")
                try:
                    product_urls = await self.scrape_category(page, url)
                    self.save_to_mongo(name, url, product_urls)
                except Exception as e:
                    self.logger.error(f"Failed scraping {name}: {e}")

            await browser.close()
        self.logger.info("Crawler finished successfully.")

    async def get_categories(self, page):
        """Extract category URLs from main category page"""
        await page.goto(self.start_url)
        await page.wait_for_selector("xpath=//a[@data-test='category-tree-navigation-button']")

        elements = await page.query_selector_all("xpath=//a[@data-test='category-tree-navigation-button']")
        categories = {}
        for el in elements:
            href = await el.get_attribute("href")
            text = (await el.inner_text()) or "Unnamed"
            if href:
                full_url = urljoin(self.start_url, href)
                categories[text.strip()] = full_url
        return categories

    async def scrape_category(self, page, category_url):
        """Scrape all product URLs for a given category (with pagination)"""
        product_urls = set()
        next_page = category_url
        page_number = 1

        while next_page:
            self.logger.info(f"Scraping page {page_number} -> {next_page}")
            await page.goto(next_page, wait_until="domcontentloaded", timeout=90000)

    
            try:
                await page.wait_for_selector("xpath=//a[@data-test='product-tile-link']", timeout=15000)
            except Exception:
                self.logger.warning(f"No products found on {next_page}")
                break

        
            prev_height = 0
            while True:
                current_height = await page.evaluate("document.body.scrollHeight")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == prev_height:
                    break
                prev_height = new_height


            items = await page.query_selector_all("xpath=//a[@data-test='product-tile-link']")
            for item in items:
                href = await item.get_attribute("href")
                if href:
                    product_urls.add(urljoin(self.start_url, href))

            self.logger.info(f"Collected {len(product_urls)} product URLs so far for {category_url}")

        
            next_btn = await page.query_selector(
                "xpath=//a[@aria-label='Next page' or @aria-label='Nächste Seite']"
            )
            if next_btn:
                href = await next_btn.get_attribute("href")
                if href:
                    next_page = urljoin(self.start_url, href)
                    page_number += 1
                else:
                    next_page = None
            else:
                next_page = None

        return list(product_urls)


    def save_to_mongo(self, category_name, category_url, product_urls):
        """Save category & product URLs to MongoDB"""
        record = {
            "category_name": category_name,
            "category_url": category_url,
            "product_urls": product_urls,
            "scraped_at": datetime.utcnow(),
        }
        self.product_urls_col.update_one(
            {"category_url": category_url}, {"$set": record}, upsert=True
        )
        self.logger.info(f"Saved {len(product_urls)} products for category: {category_name}")


if __name__ == "__main__":
    start_url = "https://shop.billa.at/kategorie"
    crawler = BillaCrawler(start_url=start_url)
    asyncio.run(crawler.run())
