import json
import math
import logging
import html as html_module
from urllib.parse import urljoin
from curl_cffi import requests
from lxml import html
from mongoengine import Document, StringField, ListField
from settings import BASE_URL, API_URL, HEADERS, PAGE_SIZE

# ---------------- SINGLE DOCUMENT MODEL ----------------
class AgentURLs(Document):
    """Single document to store all agent URLs"""
    _id = StringField(primary_key=True, default="agents")
    urls = ListField(StringField())
    meta = {"collection": "iowarealty_urls"}

class Crawler:
    """Crawl all agent profile URLs via API"""

    def fetch_agents(self, page_number: int):
        params = {
            "layoutID": 1215,
            "pageSize": PAGE_SIZE,
            "pageNumber": page_number,
            "sortBy": "lastname-asc",
        }

        try:
            resp = requests.get(API_URL, headers=HEADERS, params=params, impersonate="chrome")
            if resp.status_code != 200:
                logging.error(f"Failed page {page_number}: {resp.status_code}")
                return [], 0

            outer = json.loads(resp.text)
            data = json.loads(outer)

            html_content = html_module.unescape(data.get("Html", ""))
            total_count = data.get("TotalCount", 0)

            tree = html.fromstring(html_content)
            urls = tree.xpath("//a[contains(@class, 'site-roster-card-image-link')]/@href")
            urls = [urljoin(BASE_URL, u) for u in urls]

            return urls, total_count
        except Exception as e:
            logging.error(f"Error parsing page {page_number}: {e}")
            return [], 0

    def start(self):
        all_urls = []
        first_urls, total_count = self.fetch_agents(1)
        all_urls.extend(first_urls)

        total_pages = math.ceil(total_count / PAGE_SIZE)
        logging.info(f"Total agents: {total_count}, total pages: {total_pages}")

        for page in range(2, total_pages + 1):
            urls, _ = self.fetch_agents(page)
            all_urls.extend(urls)

        all_urls = list(dict.fromkeys(all_urls))  # remove duplicates
        logging.info(f"Collected {len(all_urls)} agent URLs")

        # ---------------- UPSERT SINGLE DOCUMENT ----------------
        AgentURLs.objects(_id="agents").update_one(
            set__urls=all_urls,
            upsert=True
        )
        logging.info("💾 All URLs saved to single MongoDB document successfully.")


if __name__ == "__main__":
    Crawler().start()
