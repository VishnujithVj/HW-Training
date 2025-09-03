import requests
from lxml import html
import re
import json

url = "https://www2.hm.com/en_in/productpage.1306054001.html"

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "origin": "https://www2.hm.com",
    "referer": "https://www2.hm.com/",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}

response = requests.get(url, headers=headers)
print("Status:", response.status_code)

# Parse HTML
tree = html.fromstring(response.content)

# Extract product title and price as before
title = tree.xpath('//h1/text()')[0].strip()
price = tree.xpath('//span[@class="a15559 b6e218 bf4f3a"]/text()')[0].strip().replace("₹", "").replace(",", "")

# Extract the JSON-LD script using regex
html_text = response.text
json_ld_matches = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html_text, re.DOTALL)
product_data = {}

for match in json_ld_matches:
    try:
        data = json.loads(match)
        if data.get("@type") == "Product":
            product_data = data
            break
    except Exception:
        continue

# Extract required fields from the JSON-LD
color = product_data.get("color")
description = product_data.get("description")
sku = product_data.get("sku")
material = product_data.get("material")
pattern = product_data.get("pattern")

print(f"Title: {title}")
print(f"Price: {price}")
print(f"Color: {color}")
print(f"Description: {description}")
print(f"SKU: {sku}")
