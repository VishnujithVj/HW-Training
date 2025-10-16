import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse
import requests
from lxml import html
from items import ProductURL
from settings import BASE_URL, HEADERS, PRODUCTS_PER_PAGE, MAX_ZERO_PAGES, REQUEST_TIMEOUT

logging.basicConfig(
    filename="bipa_crawler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}

MAIN_CATEGORIES = [
    "/c/pflege", "/c/gesundheit", "/c/ernaehrung", "/c/make-up",
    "/c/haar", "/c/baby-und-kind", "/c/haushalt", "/c/mund--und-zahnpflege",
    "/c/tier", "/c/love", "/c/parfum", "/c/weihnachten", "/c/baby-boutique",
    "/c/geschenke", "/c/themen", "/c/fotoshop"
]

def normalize_url(url):
    """Remove query parameters and trailing slash for deduplication."""
    url = url.rstrip("/")
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

def fetch_tree(url, retries=3):
    """Fetch HTML and retry if status not 200."""
    attempt = 0
    while attempt <= retries:
        try:
            r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return html.fromstring(r.text)
            logging.warning(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            logging.warning(f"Fetch error for {url}: {e}")
        attempt += 1
        time.sleep(1 + attempt)  
    return None

def get_main_categories():
    """Return full URLs for the main categories."""
    cats = [urljoin(BASE_URL, c) for c in MAIN_CATEGORIES]
    logging.info(f"Found {len(cats)} main categories.")
    return cats

def crawl_category_offset(cat_url):
    """Crawl all pages for a category."""
    seen = set()
    total_inserted = 0
    page = 0
    zero_pages = 0

    while True:
        offset = page * PRODUCTS_PER_PAGE
        paged_url = f"{cat_url}?offset={offset}"
        logging.info(f"Fetching page {page + 1}: {paged_url}")

        tree = fetch_tree(paged_url)
        if not tree:
            logging.warning(f"No HTML for {paged_url}, stopping pagination.")
            break

        links = tree.xpath('//a[contains(@href,"/p/")]/@href')
        links = [urljoin(BASE_URL, l) for l in links]
        links = list(dict.fromkeys(links))  

        inserted = 0
        for product_url in links:
            canonical_url = normalize_url(product_url)
            if canonical_url not in seen:
                seen.add(canonical_url)
                try:
                    if not ProductURL.objects(product_url=canonical_url).first():
                        ProductURL(
                            category_url=cat_url,
                            product_url=canonical_url,
                            timestamp=datetime.utcnow()
                        ).save()
                        inserted += 1
                        total_inserted += 1
                except Exception as e:
                    logging.warning(f"Failed to save {canonical_url}: {e}")

        logging.info(f"Page {page + 1}: {inserted} new URLs.")
        if inserted == 0:
            zero_pages += 1
            if zero_pages >= MAX_ZERO_PAGES:
                logging.info(f"No more pages for {cat_url}")
                break
        else:
            zero_pages = 0

        page += 1
        time.sleep(1)

    logging.info(f"Finished {cat_url}: {total_inserted} product URLs inserted.")
    return total_inserted

def main():
    logging.info(f"Starting crawler from base URL: {BASE_URL}")
    categories = get_main_categories()
    total_urls = 0

    for cat in categories:
        logging.info(f"\n=== CATEGORY START: {cat} ===")
        inserted = crawl_category_offset(cat)
        total_urls += inserted
        time.sleep(1.5)

    logging.info(f"Finished all categories. Total product URLs: {total_urls}")

if __name__ == "__main__":
    main()
