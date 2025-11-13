import json
import logging
import re
import time
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from items import ProductUrlItem, ProductItem, ProductFailedItem
from settings import HEADERS, MONGO_DB


class Parser:
    """Parse product details from Hemmings URLs"""

    def __init__(self):
        self.mongo = connect(alias="default", db=MONGO_DB, host="mongodb://localhost:27017/")
        logging.info("MongoDB connected")

    def start(self):
        urls = ProductUrlItem.objects.all()
        logging.info(f"Found {len(urls)} URLs to parse")

        for record in urls:
            url = record.url
            for attempt in range(3):

                response = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=30)
                if response.status_code == 200:
                    self.parse_item(url, response)
                    break
                else:
                    logging.warning(f"Attempt {attempt+1}: {response.status_code} for {url}")
            else:
                self.save_failed_url(url, "ConnectionError or bad status")
            time.sleep(2)


    def parse_item(self, url, response):
        sel = Selector(text=response.text)
        car_data = None

        SCRIPT_XPATH = '//script[@type="application/ld+json"]/text()'
        ENGINE_XPATH = '//h2[contains(text(),"Engine")]/following::div[@class="text-base"][1]/h3/text()'
        BODY_STYLE_XPATH = '//div[div/h2[contains(normalize-space(.),"Body Style")]]//div[@class="text-base"]/h3/text()'

        for script in sel.xpath(SCRIPT_XPATH).getall():
            try:
                data = json.loads(script.strip())
                if "@graph" in data:
                    car_data = next((i for i in data["@graph"] if i.get("@type") == "Car"), None)
                elif data.get("@type") == "Car":
                    car_data = data
                if car_data:
                    break
            except json.JSONDecodeError:
                continue

        if not car_data:
            self.save_failed_url(url, "No Car JSON-LD found")
            logging.warning(f"No JSON-LD for: {url}")
            return

        year_match = re.findall(r"\d{4}", str(car_data.get("vehicleModelDate", "")))
        year = int(year_match[0]) if year_match else None
        price = float(car_data.get("offers", {}).get("price") or 0)

        item = ProductItem(
            make=car_data.get("brand", {}).get("name"),
            model=car_data.get("model"),
            year=year,
            vin=car_data.get("vehicleIdentificationNumber"),
            price=price,
            mileage=str(car_data.get("mileageFromOdometer", {}).get("value")),
            transmission=car_data.get("vehicleTransmission"),
            engine=sel.xpath(ENGINE_XPATH).get(),
            color=car_data.get("color"),
            fuel_type=car_data.get("fuelType"),
            body_style=sel.xpath(BODY_STYLE_XPATH).get(),
            description=car_data.get("description"),
            image_urls=car_data.get("image", []),
            source_url=url,
        )

        item.save()
        logging.info(f"Parsed successfully: {url}")

    def save_failed_url(self, url, reason):
        if not ProductFailedItem.objects(url=url).first():
            ProductFailedItem(url=url, reason=reason).save()
            logging.error(f"Failed permanently: {url} ({reason})")

    def close(self):
        self.mongo.close()
        logging.info("MongoDB connection closed")

if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()
