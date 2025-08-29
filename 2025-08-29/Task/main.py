import requests
from bs4 import BeautifulSoup

class siteBikewaleParser:
    def __init__(self):
        self.base_url = "https://www.bikewale.com/new-bike-search/best-bikes-under-2-lakh/"
        self.session = requests.Session()
        self.results = []

    def fetch_html(self, url):
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def parse_data(self, html):
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.select("div.o-f7.o-o > a"):
            links.append("https://www.bikewale.com" + a.get("href"))
        return links

    def parse_item(self, url):
        html = self.fetch_html(url)
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1.o-j6.o-jm.o-jJ")
        price = soup.select_one("span.o-j5.o-jl.o-js")
        return {
            "url": url,
            "title": title.get_text(strip=True) if title else None,
            "price": price.get_text(strip=True).replace("₹", "") if price else None
        }

    def save_to_file(self, filename="bikes_data.txt"):
        with open(filename, "w", encoding="utf-8") as f:
            for item in self.results:
                f.write(str(item) + "\n")

    def start(self):
        html = self.fetch_html(self.base_url)
        if not html:
            return
        bike_urls = self.parse_data(html)
        for url in bike_urls:
            item = self.parse_item(url)
            if item:
                self.results.append(item)
        self.save_to_file()

    def close(self):
        self.session.close()


if __name__ == "__main__":
    p = siteBikewaleParser()
    p.start()
    p.close()
