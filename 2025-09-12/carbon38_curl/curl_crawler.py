import time
from urllib.parse import urljoin
from pymongo import MongoClient, errors
from curl_cffi import requests
from parsel import Selector

# --- Configurations ---
START_URL = "https://carbon38.com/en-in/collections/tops?filter.p.m.custom.available_or_waitlist=1"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "carbon38_curl"
COLLECTION_NAME = "product_urls"

# --- Headers (browser-like) ---
HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "accept-language": "en-US,en;q=0.9",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


def scrape():
    # --- Mongo Setup ---
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]
    col.create_index("url", unique=True)

    url = START_URL

    while url:
        print(f"Visiting page: {url}")
        try:
            # ✅ Use curl_cffi to fetch
            resp = requests.get(url, headers=HEADERS, impersonate="chrome110", timeout=60)
            if resp.status_code != 200:
                print(f"Failed: {resp.status_code}")
                break
        except Exception as e:
            print(f"Request error: {e}")
            break

        # Parse HTML with parsel
        sel = Selector(resp.text)

        # Extract product links
        product_links = sel.xpath(
            "//a[@class='ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage']/@href"
        ).getall()

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

        # Find next page
        next_page = sel.xpath(
            "//a[@class='Pagination__NavItem Link Link--primary' and @title='Next page']/@href"
        ).get()

        if next_page:
            url = urljoin("https://carbon38.com", next_page)
            time.sleep(2)  # polite delay
            continue

        print("No more pages. Exiting.")
        break

    client.close()


if __name__ == "__main__":
    scrape()
