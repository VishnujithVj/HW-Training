import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s", datefmt="%Y-%m-%d %H:%M:%S",)

"""Project details"""
PROJECT_NAME = "hemmings"
BASE_URL = "https://www.hemmings.com/classifieds/cars-for-sale/all-makes/1990"
ITERATION = datetime.now().strftime("%Y_%m_%d")

"""File exports"""
FILE_NAME = f"hemmings_{ITERATION}.csv"

FILE_HEADERS = [
    "make", "model", "year", "vin", "price", "mileage",
    "transmission", "engine", "color", "fuel_type", "body_style",
    "description", "image_urls", "source_url"
]

"""MongoDB setup"""
MONGO_DB = "hemmings_db"
MONGO_COLLECTION_URL = f"{PROJECT_NAME}_urls"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"
MONGO_COLLECTION_FAILED = f"{PROJECT_NAME}_failed"

"""Request headers"""
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.9',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'referer': 'https://www.hemmings.com/',
}
