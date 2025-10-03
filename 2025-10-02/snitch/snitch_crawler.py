import asyncio
import logging
from typing import List, Set

from pymongo import MongoClient, errors
from playwright.async_api import async_playwright, Page

MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "snitch_db"
COLLECTION_NAME = "product_urls"
LOG_FILE = "crawler.log"

CATEGORY_URLS = [
    "https://www.snitch.com/men-shirts/buy",
    "https://www.snitch.com/men-t-shirts/buy",
    "https://www.snitch.com/men-jeans/buy",
    "https://www.snitch.com/men-trousers/buy",
    "https://www.snitch.com/men-overshirt/buy",
    "https://www.snitch.com/men-cargo-pants/buy",
    "https://www.snitch.com/men-hoodies-and-sweatshirts/buy",
    "https://www.snitch.com/men-shorts/buy",
    "https://www.snitch.com/men-joggers-and-trackpants/buy",
    "https://www.snitch.com/men-jackets/buy",
]

EXTRA_HTTP_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "connection": "keep-alive",
    "origin": "https://www.snitch.com",
    "referer": "https://www.snitch.com/",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
}

SCROLL_WAIT = 10  # wait 10 seconds for new products
BROWSER_HEADLESS = False
MAX_PRODUCTS_PER_CATEGORY = 500  # <-- Set the max products per category here


class SnitchCrawler:
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("SnitchCrawler")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        try:
            self.collection.create_index("url", unique=True)
        except Exception as e:
            self.logger.warning(f"Could not create index: {e}")

    async def extract_product_links_via_dom(self, page: Page) -> Set[str]:
        js = """
        () => {
            const urls = new Set();
            function collectFrom(container) {
                if (!container) return;
                const anchors = container.querySelectorAll('a');
                anchors.forEach(a => {
                    try {
                        if (a.querySelector && a.querySelector('img')) {
                            const href = a.href || a.getAttribute('href');
                            if (href && !href.startsWith('javascript:')) urls.add(href);
                        }
                    } catch {}
                });
            }
            const possibleContainers = [
                document.querySelector('[data-test*="product"]'),
                document.querySelector('.product-grid'),
                document.querySelector('.products'),
                document.querySelector('.catalog'),
                document.querySelector('main')
            ];
            for (const c of possibleContainers) collectFrom(c);
            collectFrom(document);
            return Array.from(urls);
        }
        """
        try:
            hrefs = await page.evaluate(js)
            return set(hrefs)
        except Exception as e:
            self.logger.error(f"DOM extraction error: {e}")
            return set()

    async def scroll_last_product_into_view(self, page: Page) -> int:
        js = """
        () => {
            try {
                const anchors = Array.from(document.querySelectorAll('a')).filter(a => {
                    try { return !!a.querySelector && !!a.querySelector('img') && (a.href || a.getAttribute('href')); }
                    catch { return false; }
                });
                if (!anchors.length) {
                    window.scrollBy(0, window.innerHeight);
                    return 0;
                }
                anchors[anchors.length - 1].scrollIntoView({behavior: 'auto', block: 'center'});
                return anchors.length;
            } catch {
                try { window.scrollBy(0, window.innerHeight); } catch {}
                return 0;
            }
        }
        """
        try:
            return int(await page.evaluate(js) or 0)
        except Exception:
            await page.evaluate("window.scrollBy(0, window.innerHeight);")
            return 0

    async def scroll_until_end(self, page: Page) -> Set[str]:
        collected = set(await self.extract_product_links_via_dom(page))
        self.logger.info(f"Initial products found: {len(collected)}")

        previous_height = -1
        while True:
            # Stop if we reached max products
            if MAX_PRODUCTS_PER_CATEGORY and len(collected) >= MAX_PRODUCTS_PER_CATEGORY:
                self.logger.info(f"Reached max products limit: {MAX_PRODUCTS_PER_CATEGORY}")
                collected = set(list(collected)[:MAX_PRODUCTS_PER_CATEGORY])
                break

            # Get current page height
            current_height = await page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                self.logger.info("Reached end of page, no more products.")
                break

            previous_height = current_height
            await self.scroll_last_product_into_view(page)
            await asyncio.sleep(SCROLL_WAIT)

            new_links = await self.extract_product_links_via_dom(page)
            added = len(new_links - collected)
            collected.update(new_links)
            self.logger.info(f"Total collected: {len(collected)} (added {added})")

        return collected

    async def crawl_category(self, page: Page, category_url: str) -> Set[str]:
        self.logger.info(f"Crawling category: {category_url}")
        try:
            await page.goto(category_url, wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            self.logger.warning(f"Timeout or load issue at {category_url}, continuing.")

        collected = await self.scroll_until_end(page)
        self.logger.info(f"Finished crawling {category_url}. Total collected: {len(collected)}")
        return collected

    def save_one(self, url: str, source_category: str):
        doc = {"url": url, "source": source_category}
        try:
            self.collection.insert_one(doc)
            self.logger.info(f"Inserted: {url}")
        except errors.DuplicateKeyError:
            self.logger.debug(f"Skipped duplicate: {url}")
        except Exception as e:
            self.logger.error(f"Mongo insert error for {url}: {e}")

    async def run(self, category_urls: List[str]):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=BROWSER_HEADLESS)
            context = await browser.new_context(extra_http_headers=EXTRA_HTTP_HEADERS)
            page = await context.new_page()

            for cat in category_urls:
                try:
                    product_urls = await self.crawl_category(page, cat)
                    for url in product_urls:
                        self.save_one(url, cat)
                except Exception as e:
                    self.logger.exception(f"Error crawling {cat}: {e}")

            await browser.close()
            self.logger.info("Crawl finished.")


async def main():
    crawler = SnitchCrawler(MONGODB_URI, DB_NAME, COLLECTION_NAME)
    await crawler.run(CATEGORY_URLS)


if __name__ == "__main__":
    asyncio.run(main())
