import requests
from lxml import html

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

# Parse the HTML
html_content = html.fromstring(response.content)

# Extract and clean
title = html_content.xpath('//h1/text()')
price = html_content.xpath('//span[@class="a15559 b6e218 bf4f3a"]/text()')

print(f"Title: {title}")
print(f"Price: {price}")

