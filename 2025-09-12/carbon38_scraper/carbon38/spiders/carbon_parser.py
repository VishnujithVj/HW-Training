import scrapy
import json
from w3lib.html import remove_tags
from pymongo import MongoClient
from carbon38.items import Carbon38ScraperItem

class ProductDetailsSpider(scrapy.Spider):
    name = "product_details"
    allowed_domains = ["carbon38.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mongo_uri = kwargs.get("mongo_uri", "mongodb://localhost:27017")
        mongo_db = kwargs.get("mongo_db", "carbon38")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[mongo_db]

    def start_requests(self):
        # Read product URLs from MongoDB
        urls = self.db["product_urls"].find({}, {"url": 1, "_id": 0})
        for entry in urls:
            yield scrapy.Request(entry["url"], callback=self.parse_product)

    def parse_product(self, response):
        json_text = response.xpath(
            '//script[@type="application/json" and @data-product-json]/text()'
        ).get()
        if not json_text:
            self.logger.warning(f"No JSON found on: {response.url}")
            return

        data = json.loads(json_text)
        product = data.get("product", {})
        variants = product.get("variants", [])

        item = Carbon38ScraperItem()
        featured = product.get("featured_image") or ""
        item["primary_image_url"] = "https:" + featured if featured else ""
        item["brand"] = product.get("vendor", "")
        item["product_name"] = product.get("title", "")

        if variants:
            price_int = int(variants[0].get("price", 0))
            item["price"] = f"₹{price_int/100:.2f}"
            item["colour"] = variants[0].get("option1", "")
            item["sizes"] = [v.get("option2", "") for v in variants if v.get("option2")]
            item["sku"] = variants[0].get("sku", "")
        else:
            item["price"] = "₹0.00"
            item["colour"] = ""
            item["sizes"] = []
            item["sku"] = ""

        description = product.get("description") or ""
        item["description"] = remove_tags(description).strip()
        item["reviews"] = "0 Reviews" 
        item["product_id"] = str(product.get("id", ""))
        item["product_url"] = response.url
        item["image_urls"] = [
            "https:" + img for img in product.get("images", []) if img
        ]

        yield item
