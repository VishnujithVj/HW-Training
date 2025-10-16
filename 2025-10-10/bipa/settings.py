import logging
from mongoengine import connect

PROJECT_NAME = "bipa"
BASE_URL = "https://www.bipa.at"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    )
}

PRODUCTS_PER_PAGE = 20
MAX_ZERO_PAGES = 3
REQUEST_TIMEOUT = 15

logging.basicConfig(
    filename=f"{PROJECT_NAME}.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

connect(
    db=f"{PROJECT_NAME}_db",
    host=f"mongodb://localhost:27017/{PROJECT_NAME}_db",
)
