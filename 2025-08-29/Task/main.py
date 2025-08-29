import requests
from bs4 import BeautifulSoup

class DataMiningError(Exception):
    """Custom exception for data mining errors."""
    def __init__(self, message, url=None):
        super().__init__(message)
        self.message = message
        self.url = url

    def __str__(self):
        if self.url:
            return f"{self.message} (URL: {self.url})"
        return self.message

class siteBikewaleParser:
    def __init__(self):
        self.base_url = "https://www.bikewale.com/new-bike-search/best-bikes-under-2-lakh/"
        self.session = requests.Session()
        self.results = []

    def fetch_html(self, url, save_raw=False):
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            if save_raw:
                with open("raw.html", "w", encoding="utf-8") as f:
                    f.write(r.text)
            return r.text
        except requests.ConnectionError as e:
            print(f"Connection error while fetching {url}: {e}")
            return None
        except requests.HTTPError as e:
            print(f"HTTP error while fetching {url}: {e}")
            return None
        except requests.RequestException as e:
            print(f"Request exception while fetching {url}: {e}")
            return None

    def parse_data(self, html):
        try:
            soup = BeautifulSoup(html, "html.parser")
            links = []
            for a in soup.select("div.o-f7.o-o > a"):
                href = a.get("href")
                if not href:
                    continue
                links.append("https://www.bikewale.com" + href)
            if not links:
                raise DataMiningError("No bike links found in the HTML.")
            return links
        except Exception as e:
            raise DataMiningError(f"Failed to parse data: {e}")

    def parse_item(self, url):
        html = self.fetch_html(url)
        if not html:
            return None
        try:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.select_one("h1.o-j6.o-jm.o-jJ")
            price = soup.select_one("span.o-j5.o-jl.o-js")
            if not title or not price:
                raise DataMiningError("Missing title or price", url=url)
            return {
                "url": url,
                "title": title.get_text(strip=True),
                "price": price.get_text(strip=True).replace("₹", "")
            }
        except Exception as e:
            raise DataMiningError(f"Failed to parse item: {e}", url=url)

    def save_links_to_file(self, links, filename="links.txt"):
        with open(filename, "w", encoding="utf-8") as f:
            for link in links:
                f.write(link + "\n")

    def yield_lines_from_file(self, filename):
        """Generator that yields lines from a file one by one."""
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                yield line.strip()

    def save_to_file(self, filename="cleaned_data.txt"):
        with open(filename, "w", encoding="utf-8") as f:
            for item in self.results:
                f.write(str(item) + "\n")

    def start(self):
        html = self.fetch_html(self.base_url, save_raw=True)
        if not html:
            return
        try:
            bike_urls = self.parse_data(html)
        except DataMiningError as e:
            print(e)
            return
        self.save_links_to_file(bike_urls, "links.txt")
        for url in self.yield_lines_from_file("links.txt"):
            try:
                item = self.parse_item(url)
                if item:
                    self.results.append(item)
            except DataMiningError as e:
                print(e)
        self.save_to_file()

    def close(self):
        self.session.close()


if __name__ == "__main__":
    p = siteBikewaleParser()
    p.start()
    p.close()
