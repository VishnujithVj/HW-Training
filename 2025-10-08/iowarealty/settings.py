import logging
from mongoengine import connect

# ---------------- BASIC CONFIG ----------------
PROJECT_NAME = "iowarealty"
BASE_URL = "https://www.iowarealty.com"
START_URL = f"{BASE_URL}/roster/Agents"
API_URL = f"{BASE_URL}/CMS/CmsRoster/RosterSearchResults"

# ---------------- MONGO CONNECTION ----------------
connect(
    db=f"{PROJECT_NAME}_db",
    host=f"mongodb://localhost:27017/{PROJECT_NAME}_db",
    alias="default"
)

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------- HEADERS ----------------
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9",
    "referer": START_URL,
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}

COLL_URLS = f"{PROJECT_NAME}_urls"
COLL_DATA = f"{PROJECT_NAME}_data"
COLL_FAILED = f"{PROJECT_NAME}_failed"

PAGE_SIZE = 10
