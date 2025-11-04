""" FEASIBILITY WORK REPORT - FATFACE.COM """

from curl_cffi import requests
from parsel import Selector
from urllib.parse import urljoin
import math
import time

""" CONFIG """
BASE_URL = "https://www.fatface.com"
START_URL = "https://www.fatface.com/shop/f/feat-newin?p=1"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


""" CRAWLER """
page = 1
total_products = 0
product_urls = []

while True:
    page_url = f"{START_URL.split('?')[0]}?p={page}"

    response = requests.get(page_url, headers=HEADERS,timeout=30)
    sel = Selector(text=response.text)

    """ Extract product count """
    if page == 1:
        count_text = sel.xpath('//span[@class="esi-count"]/text()').get()
        if count_text:
            digits = "".join([c for c in count_text if c.isdigit()])
            total_products = int(digits) if digits else 0


    """ Extract product URLs """
    links = sel.xpath('//a[contains(@class,"MuiCardMedia-root") and @href]/@href').getall()
    links = [urljoin(BASE_URL, href.split("#")[0]) for href in links if href.strip()]
    product_urls.extend(links)

    """ Pagination logic """
    if total_products and len(links) > 0:
        per_page = len(links)
        total_pages = math.ceil(total_products / per_page)
        if page >= total_pages:
            break

    page += 1
    time.sleep(1)


""" PARSER """
PRODUCT_TITLE = '//h1[@data-testid="product-title"]/text()'
PRODUCT_PRICE = '//div[@data-testid="product-now-price"]/span/text()'
PRODUCT_COLOUR = '//span[@data-testid="selected-colour-label"]/text()'
PRODUCT_DESCRIPTION = '//p[@data-testid="item-description"]/text()'
PRODUCT_CODE = '//div[@class="MuiBox-root pdp-css-lhfv11"]/span/text()'

results = []

for idx, url in enumerate(product_urls[:50]):  

    res = requests.get(url, headers=HEADERS,timeout=20)
    if res.status_code != 200:
        continue

    sel = Selector(text=res.text)

    title = sel.xpath(PRODUCT_TITLE).get()
    price = sel.xpath(PRODUCT_PRICE).get()
    colour = sel.xpath(PRODUCT_COLOUR).get()
    description = sel.xpath(PRODUCT_DESCRIPTION).get()
    product_id = sel.xpath(PRODUCT_CODE).get()

    product_data = {
        "url": url,
        "title": title.strip() if title else None,
        "price": price.strip() if price else None,
        "colour": colour.strip() if colour else None,
        "description": description.strip() if description else None,
        "product_id": product_id.strip() if product_id else None,
        "status": res.status_code,
    }

    results.append(product_data)


("############################## FINDINGS ##############################")

("""
- The site implements infinite scroll pagination. The crawler must programmatically generate scroll events to load all content and collect the product URLs.
- Product listing  pagination like this (?p=1, ?p=2, ...).
- Product count available under //span[@class="esi-count"].
- Product URLs extracted from <a class="MuiCardMedia-root ..."> tags.
- All visible fields can be  extracted.
- Available Product details (title, price, colour, review, description, product_id, fit, care & fabric) are accessible in  HTML.
- Crawling can proceed safely using polite delays.
""")
