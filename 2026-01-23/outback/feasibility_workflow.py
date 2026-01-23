import requests
import json
from parsel import Selector

BASE_URL = "https://www.outback.com"
LOCATION = "maumee"
URL = f"{BASE_URL}/menu/{LOCATION}/category/0"

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# -------- crawler ----------------
def fetch_category():
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    selector = Selector(text=resp.text)
    next_data_text = selector.xpath('//script[@id="__NEXT_DATA__"]/text()').get()

    if not next_data_text:
        raise ValueError("__NEXT_DATA__ not found")

    next_data = json.loads(next_data_text)

    categories = (
        next_data
        .get("props", {})
        .get("pageProps", {})
        .get("params", {})
        .get("restaurantMenu", {})
        .get("categories", [])
    )

    if not categories:
        raise ValueError("restaurantMenu.categories not found")

    results = []

    for category in categories:
        category_id = category.get("id")
        category_name = category.get("name")

        category_url = (
            f"{BASE_URL}/menu/{LOCATION}/category/{category_id}"
            if category_id else None
        )

        for product in category.get("products", []):
            product_id = product.get("id")

        # product details
            results.append({
                "category_id": category_id,
                "category_name": category_name,
                "category_url": category_url,
                "product_id": product_id,
                "product_name": product.get("name"),
                "product_url": (f"{BASE_URL}/menu/{LOCATION}/category/{category_id}/product/{product_id}"
                    if category_id and product_id else None),
                "price": product.get("cost"),
                "description": product.get("description"),
                "image_url": (f"https://media.outback.com/{product.get('imagefilename')}"
                    if product.get("imagefilename") else None),
                "calories": product.get("basecalories"),

            })
    return results
