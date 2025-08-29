import logging

# Constants
BASE_URL = "https://www.bikewale.com/new-bike-search/best-bikes-under-2-lakh/"
RAW_HTML_FILE = "raw.html"
LINKS_FILE = "links.txt"
CLEANED_DATA_FILE = "cleaned_data.txt"
LOG_FILE = "parser.log"

# Logging configuration
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Exceptions
class DataMiningError(Exception):
    """Custom exception for data mining errors."""
    def __init__(self, message, url=None):
        super().__init__(message)
        self.message = message
        self.url = url

    def __str__(self):
        if self.url:
            return f"{self.message} (URL: {self.url})"
        return self.message

# Helper functions
def save_to_file(filename, items):
    with open(filename, "w", encoding="utf-8") as f:
        for item in items:
            f.write(str(item) + "\n")

def yield_lines_from_file(filename):
    """Generator that yields lines from a file one by one."""
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            yield line.strip()