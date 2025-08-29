import requests
from bs4 import BeautifulSoup
from settings import (
    BASE_URL, RAW_HTML_FILE, LINKS_FILE, CLEANED_DATA_FILE,
    logger, DataMiningError, save_to_file, yield_lines_from_file
)

class siteBikewaleParser:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.results = []

    def fetch_html(self, url, save_raw=False):
        try:
            logger.info(f"Fetching HTML from {url}")
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            if save_raw:
                with open(RAW_HTML_FILE, "w", encoding="utf-8") as f:
                    f.write(r.text)
                logger.info(f"Saved raw HTML to {RAW_HTML_FILE}")
            return r.text
        except requests.ConnectionError as e:
            logger.error(f"Connection error while fetching {url}: {e}")
            return None
        except requests.HTTPError as e:
            logger.error(f"HTTP error while fetching {url}: {e}")
            return None
        except requests.RequestException as e:
            logger.error(f"Request exception while fetching {url}: {e}")
            return None

    def parse_data(self, html):
        try:
            logger.info("Parsing bike links from HTML")
            soup = BeautifulSoup(html, "html.parser")
            links = []
            for a in soup.select("div.o-f7.o-o > a"):
                href = a.get("href")
                if not href:
                    continue
                links.append(f"https://www.bikewale.com{href}")
            if not links:
                raise DataMiningError("No bike links found in the HTML.")
            logger.info(f"Found {len(links)} bike links")
            return links
        except Exception as e:
            raise DataMiningError(f"Failed to parse data: {e}")

    def parse_item(self, url):
        html = self.fetch_html(url)
        if not html:
            return None
        try:
            logger.info(f"Parsing item from {url}")
            soup = BeautifulSoup(html, "html.parser")
            title = soup.select_one("h1.o-j6.o-jm.o-jJ")
            price = soup.select_one("span.o-j5.o-jl.o-js")
            if not title or not price:
                raise DataMiningError("Missing title or price", url=url)
            logger.info(f"Parsed item: {title.get_text(strip=True)} - {price.get_text(strip=True)}")
            return {
                "url": url,
                "title": title.get_text(strip=True),
                "price": price.get_text(strip=True).replace("₹", "")
            }
        except Exception as e:
            raise DataMiningError(f"Failed to parse item: {e}", url=url)

    def save_links_to_file(self, links, filename=LINKS_FILE):
        with open(filename, "w", encoding="utf-8") as f:
            for link in links:
                f.write(f"{link}\n")
        logger.info(f"Saved {len(links)} links to {filename}")

    def start(self):
        logger.info("Starting Bikewale parser")
        html = self.fetch_html(self.base_url, save_raw=True)
        if not html:
            logger.info("No HTML fetched, exiting.")
            return
        try:
            bike_urls = self.parse_data(html)
        except DataMiningError as e:
            logger.error(str(e))
            return
        self.save_links_to_file(bike_urls, LINKS_FILE)
        for url in yield_lines_from_file(LINKS_FILE):
            try:
                item = self.parse_item(url)
                if item:
                    self.results.append(item)
            except DataMiningError as e:
                logger.error(str(e))
        save_to_file(CLEANED_DATA_FILE, self.results)
        logger.info(f"Saved cleaned data to {CLEANED_DATA_FILE}")

    def close(self):
        self.session.close()
        logger.info("Closed session")


if __name__ == "__main__":
    p = siteBikewaleParser()
    p.start()
    p.close()

    # New example list of dictionaries
    items = [
        {"title": "Bike Alpha", "price": 120000},
        {"title": "Bike Beta", "price": None},
        {"title": "Bike Gamma", "price": 95000},
        {"title": "Bike Delta", "price": None},
        {"title": "Bike Epsilon", "price": 110000}
    ]

    # 1. Extract only product titles from the list of dictionaries
    titles = [item["title"] for item in items]
    print(f"Titles: {titles}")

    # 2. Filter out entries with null prices
    items_with_price = [item for item in items if item.get("price") is not None]
    print(f"Items with price: {items_with_price}")