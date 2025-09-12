from pymongo import MongoClient

class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'carbon38')
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

        # Each spider saves to its own collection
        if spider.name == "product_urls":
            self.collection = self.db["product_urls"]
        elif spider.name == "product_details":
            self.collection = self.db["product_data"]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # Upsert by unique key
        if spider.name == "product_urls":
            self.collection.update_one({"url": item["url"]}, {"$set": dict(item)}, upsert=True)
        elif spider.name == "product_details":
            self.collection.update_one({"product_id": item["product_id"]}, {"$set": dict(item)}, upsert=True)
        return item
