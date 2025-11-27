import requests
from parsel import Selector
from urllib.parse import urljoin
import datetime
import json
import time

##############################################################
# SECTION 1 — CRAWLER
##############################################################

BASE_URL = "https://sa.aqar.fm/"
OUTPUT_FILE = "aqar_all_urls.txt"

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}


def save_url(url):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

    resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
    sel = Selector(resp.text)

    categories = sel.xpath('//div[contains(@class, "_list__")]/a')

    for cat in categories:
        cat_name = cat.xpath('string(.)').get().strip()
        cat_href = cat.xpath('./@href').get()
        cat_base_url = urljoin(BASE_URL, cat_href).rstrip("/")
        save_url(cat_base_url)

        page_num = 1

        while True:
            page_url = f"{cat_base_url}/{page_num}"
            print(f"Scraping Page {page_num}: {page_url}")

            try:
                page_resp = requests.get(page_url, headers=HEADERS, timeout=10)
            except:
                break

            page_sel = Selector(page_resp.text)

            product_links = page_sel.xpath(
                '//div[contains(@class, "_list__")]/div/a/@href'
            ).getall()

            if not product_links:
                print("No listings found → stop pagination")
                break

            for link in product_links:
                full_url = urljoin(BASE_URL, link)
                save_url(full_url)

            page_num += 1
            time.sleep(0.5)


##############################################################
# SECTION 2 — PARSER
##############################################################

def parse_property(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        sel = Selector(resp.text)
    except Exception as e:
        return {"url": url, "error": f"Request failed: {e}"}

    data = {}

    # ID fields
    data["id"] = sel.xpath(
        '//div[contains(@class, "_item___4Sv8")][span[contains(text(), "Ad number")]]'
        '/following-sibling::div//span/text()'
    ).get()

    data["reference_number"] = data["id"]
    data["url"] = url
    data["category"] = sel.xpath(
        '//div[contains(@class, "_auction__")]//h2/text()'
    ).get()

    data["category_url"] = url
    data["title"] = data["category"]

    data["description"] = sel.xpath(
        '//div[contains(@class, "_root__")]//p/text()'
    ).get()

    data["location"] = sel.xpath(
        '//div[contains(@class, "_approvedPreciseLocation__")]//span/text()'
    ).get()

    data["price"] = sel.xpath(
        '//h2[contains(@class, "_price__")]//span/text()'
    ).get()
    data["currency"] = "SAR"
    data["price_per"] = sel.xpath(
        '//h2[contains(@class, "_price__")]/font/text()'
    ).get()
    data["bedrooms"] = sel.xpath(
        '//div[contains(@class, "_item___4Sv8")][div[contains(text(), "bedrooms")]]'
        '/following-sibling::div/text()'
    ).get()

    data["bathrooms"] = None
    data["scraped_ts"] = datetime.datetime.now().isoformat()
    amenities = sel.xpath('//div[contains(@class, "_boolean__")]/font/text()').getall()
    data["amenities"] = ", ".join(amenities) if amenities else None

    area = sel.xpath(
        '//div[contains(@class, "_item___4Sv8")][div[contains(text(), "Area")]]'
        '/following-sibling::div/text()'
    ).get()

    details = []
    if area:
        details.append(f"Area: {area}")

    data["details"] = " | ".join(details) if details else None
    data["agent_name"] = sel.xpath(
        '//h2[contains(@class, "_name__")]/text()'
    ).get()
    data["number_of_photos"] = None
    data["phone_number"] = None

    data["date"] = sel.xpath(
        '//div[contains(@class, "_item___4Sv8")][span[contains(text(), "Date Added")]]/span/text()'
    ).get()
    data["property_type"] = data["category"]
    data["published_at"] = data["date"]

    return data


##############################################################
# FINDINGS 
##############################################################





