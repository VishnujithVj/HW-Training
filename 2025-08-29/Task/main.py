import requests
from bs4 import BeautifulSoup
from settings import (
    BASE_URL, RAW_HTML_FILE, LINKS_FILE, CLEANED_DATA_FILE,
    logger, DataMiningError, save_to_file, yield_lines_from_file
)


class SiteBikewaleParser:
    """
    Parser class for extracting bike data from Bikewale website.
    Handles fetching, parsing, and saving of bike information.
    """

    def __init__(self):
        """Initialize parser with base URL, session, and results list."""
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.results = []

    def fetch_html(self, url, save_raw=False):
        """
        Fetch HTML content from a given URL.
        Optionally saves the raw HTML to a file.
        Handles connection and HTTP errors gracefully.

        Args:
            url (str): The URL to fetch.
            save_raw (bool): Whether to save the raw HTML to a file.

        Returns:
            str or None: HTML content as string, or None if fetch fails.
        """
        try:
            logger.info(f"Fetching HTML from {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            if save_raw:
                with open(RAW_HTML_FILE, "w", encoding="utf-8") as f:
                    f.write(response.text)
                logger.info(f"Saved raw HTML to {RAW_HTML_FILE}")
            return response.text
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
        """
        Parse the main page HTML to extract bike links.

        Args:
            html (str): HTML content of the main page.

        Returns:
            list: List of bike detail page URLs.

        Raises:
            DataMiningError: If parsing fails or no links are found.
        """
        try:
            logger.info("Parsing bike links from HTML")
            soup = BeautifulSoup(html, "html.parser")
            links = [
                f"https://www.bikewale.com{a.get('href')}"
                for a in soup.select("div.o-f7.o-o > a")
                if a.get("href")
            ]
            if not links:
                raise DataMiningError("No bike links found in the HTML.")
            logger.info(f"Found {len(links)} bike links")
            return links
        except Exception as e:
            raise DataMiningError(f"Failed to parse data: {e}")

    def parse_item(self, url):
        """
        Parse a bike detail page to extract title and price.

        Args:
            url (str): URL of the bike detail page.

        Returns:
            dict or None: Dictionary with bike data, or None if fetch fails.

        Raises:
            DataMiningError: If parsing fails or required data is missing.
        """
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
            logger.info(
                f"Parsed item: {title.get_text(strip=True)} - {price.get_text(strip=True)}"
            )
            return {
                "url": url,
                "title": title.get_text(strip=True),
                "price": price.get_text(strip=True).replace("₹", "")
            }
        except Exception as e:
            raise DataMiningError(f"Failed to parse item: {e}", url=url)

    def save_links_to_file(self, links, filename=LINKS_FILE):
        """
        Save a list of links to a text file.

        Args:
            links (list): List of URLs to save.
            filename (str): File path to save the links.
        """
        with open(filename, "w", encoding="utf-8") as f:
            for link in links:
                f.write(f"{link}\n")
        logger.info(f"Saved {len(links)} links to {filename}")

    def start(self):
        """
        Main method to start the parsing process.
        Fetches main page, extracts links, parses each bike, and saves results.
        """
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
        """Close the HTTP session."""
        self.session.close()
        logger.info("Closed session")


if __name__ == "__main__":
    # Run the Bikewale parser
    parser = SiteBikewaleParser()
    parser.start()
    parser.close()

    # --- List comprehension examples for demonstration ---

    # Example list of dictionaries representing products
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