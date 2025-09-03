# 

import requests
from lxml import html
from urllib.parse import urljoin

base_url = "https://www.marksandspencer.com/"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
}

# Step 1: Fetch Homepage
response = requests.get(base_url, headers=headers, timeout=20)
print("Homepage status:", response.status_code)

tree = html.fromstring(response.content)

# Step 2: Extract Category Links (Women, Men, Kids, etc.)
category_links = tree.xpath('//a[contains(@class,"analytics-department-carousel_cardWrapper")]/@href')

# Make absolute URLs
category_links = [urljoin(base_url, link) for link in category_links]
category_links = list(set(category_links))  # remove duplicates

print("\nTop Categories:")
for link in category_links:
    print(link)

# Step 3: For each category, get Sub-Category Links
for cat_url in category_links:
    print(f"\nFetching category: {cat_url}")
    try:
        resp = requests.get(cat_url, headers=headers, timeout=20)
        sub_tree = html.fromstring(resp.content)

        # Sub-category links inside circular navigation
        sub_links = sub_tree.xpath('//nav[contains(@class,"circular-navigation_circularNavigationBox")]//a/@href')

        sub_links = [urljoin(base_url, s) for s in sub_links]
        sub_links = list(set(sub_links))  # unique links

        print(f"  Found {len(sub_links)} sub-categories:")
        for s in sub_links:
            print("   ", s)

    except Exception as e:
        print("  Error fetching:", e)
