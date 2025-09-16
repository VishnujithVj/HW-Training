import scrapy
import json
import time
import psutil
import logging
from w3lib.html import remove_tags
from pymongo import MongoClient
from carbon38.items import Carbon38ScraperItem


class ProductDetailsSpider(scrapy.Spider):
    name = "product_details"
    allowed_domains = ["carbon38.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # MongoDB setup
        mongo_uri = kwargs.get("mongo_uri", "mongodb://localhost:27017")
        mongo_db = kwargs.get("mongo_db", "carbon38")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[mongo_db]

        # Logging setup
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler()],
        )

        # Track execution time
        self.start_time = time.time()

    def start_requests(self):
        """Fetch product URLs from MongoDB and start scraping."""
        product_urls = self.db["product_urls"].find({}, {"url": 1, "_id": 0})

        for entry in product_urls:
            yield scrapy.Request(entry["url"], callback=self.parse_product)

    def parse_product(self, response):
        """Parse individual product details from product page JSON."""

        self.logger.info(f"Response: {response.status} | {response.url}")

        json_text = response.xpath(
            '//script[@type="application/json" and @data-product-json]/text()'
        ).get()

        if not json_text:
            self.logger.warning(f"No product JSON found on: {response.url}")
            return

        try:
            product_data = json.loads(json_text).get("product", {})
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON on: {response.url}")
            return

        variants = product_data.get("variants", [])

        item = Carbon38ScraperItem()
        featured_img = product_data.get("featured_image") or ""

        item["primary_image_url"] = f"https:{featured_img}" if featured_img else ""
        item["brand"] = product_data.get("vendor", "")
        item["product_name"] = product_data.get("title", "")

        if variants:
            first_variant = variants[0]
            price_int = int(first_variant.get("price", 0))
            item["price"] = f"₹{price_int/100:.2f}"
            item["colour"] = first_variant.get("option1", "")
            item["sizes"] = [v.get("option2", "") for v in variants if v.get("option2")]
            item["sku"] = first_variant.get("sku", "")
        else:
            item["price"] = "₹0.00"
            item["colour"] = ""
            item["sizes"] = []
            item["sku"] = ""

        description = product_data.get("description") or ""
        item["description"] = remove_tags(description).strip()
        item["reviews"] = "0 Reviews" 
        item["product_id"] = str(product_data.get("id", ""))
        item["product_url"] = response.url
        item["image_urls"] = [
            f"https:{img}" for img in product_data.get("images", []) if img
        ]

        yield item

    def closed(self, reason):
        """Log time and memory usage when spider finishes."""
        end_time = time.time()
        total_time = end_time - self.start_time
        memory_used = psutil.Process().memory_info().rss / (1024 * 1024)

        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Execution Time: {total_time:.2f} seconds")
        self.logger.info(f"Memory Usage: {memory_used:.2f} MB")
        
