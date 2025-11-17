import logging
import time
from urllib.parse import unquote
from curl_cffi import requests
from parsel import Selector
from mongoengine import connect
from settings import HEADERS, MONGO_DB, MONGO_HOST
from items import PropertyCategoryItem, PropertyPostUrlItem


class Crawler:
    """Haraj Posts Crawler for each subcategory/tag"""

    GRAPHQL_URL = (
        "https://graphql.haraj.com.sa/?queryName=posts&"
        "clientId=WgwbWHtZ-KBrh-hrBl-Qfxx-M9ulgh9qHxpQv3&"
        "version=N0.0.1%20,%202025-11-12%2003/"
    )

    QUERY = """
    query FetchAds($page: Int, $tag: String, $beforeUpdateDate: Int) {
      posts(page: $page, tag: $tag, beforeUpdateDate: $beforeUpdateDate) {
        items {id title URL updateDate}
        pageInfo { hasNextPage }
      }
    }
    """

    def __init__(self):
        self.mongo = connect(alias="default",db=MONGO_DB,host=MONGO_HOST)
        logging.info("MongoDB connected")

    def extract_tag_name(self, url: str):
        """Extract Arabic tag from tag URL"""
        return unquote(url.split("/tags/")[-1])

    def start(self):
        """Entry point — Load category URLs from DB and crawl"""
        categories = PropertyCategoryItem.objects()

        if not categories:
            logging.error("No category URLs found in DB.")
            return

        for cat in categories:
            url = cat.url
            tag = self.extract_tag_name(url)

            meta = {
                "category": tag,
                "tag": tag,
                "page": 1,
                "before_update_date": None
            }

            logging.info(f"Starting tag: {tag}")
            self.crawl_tag(meta)


    def crawl_tag(self, meta):
        """Crawl one tag using pagination logic similar to others"""

        tag = meta["tag"]
        page = meta["page"]
        before_update_date = meta["before_update_date"]

        while True:
            """Build GraphQL payload"""
            variables = {
                "tag": tag,
                "page": page,
                "beforeUpdateDate": before_update_date,
            }

            payload = {
                "queryName": "posts",
                "clientId": "WgwbWHtZ-KBrh-hrBl-Qfxx-M9ulgh9qHxpQv3",
                "version": "N0.0.1 , 2025-11-12 03/",
                "query": self.QUERY,
                "variables": variables,
            }

            logging.info(f"Fetching page {page} for tag: {tag}")

            try:
                response = requests.post(
                    self.GRAPHQL_URL,
                    headers=HEADERS,
                    json=payload,
                    timeout=30,
                )
                data = response.json()
            except Exception as e:
                logging.error(f"Request failed: {e}")
                return

            """Parse response"""
            is_next = self.parse_item(data, meta)
            if not is_next:
                logging.info("✔ Pagination completed for this tag.")
                break

            """Update pagination offsets"""
            page = meta["page"]
            before_update_date = meta["before_update_date"]
            time.sleep(1.2)

    def parse_item(self, data, meta):
        """Extract posts and save to DB (Template-style parser)"""
        posts = data.get("data", {}).get("posts", {}).get("items", [])

        if not posts:
            return False

        tag = meta.get("tag")
        update_dates = []

        for p in posts:
            try:
                full_url = "https://haraj.com.sa/" + p.get("URL", "").lstrip("/")
                item = PropertyPostUrlItem(
                    tag=tag,
                    title=p.get("title", ""),
                    url=full_url,
                    update_date=p.get("updateDate")
                )
                item.save()
                update_dates.append(p.get("updateDate"))

                logging.info(f"Saved: {full_url}")
            except Exception as e:
                logging.error(f"DB Save Error: {e}")

        """pagination update"""
        if update_dates:
            meta["before_update_date"] = min(update_dates)
            meta["page"] = meta.get("page") + 1
            return True
        return False

    def close(self):
        self.mongo.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    crawler = Crawler()
    crawler.start()
    crawler.close()
