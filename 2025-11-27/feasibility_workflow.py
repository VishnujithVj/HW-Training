import requests
from parsel import Selector
import datetime
from urllib.parse import urljoin

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}

base_url = "https://sa.aqar.fm/"
output_file = "aqar_urls.txt"
property_output_file = "aqar_properties.json"

# =========== crawer ====================
all_urls = []
all_properties = []
response = requests.get(base_url, headers=headers, timeout=10)
sel = Selector(response.text)

categories = sel.xpath('//div[contains(@class, "_list__")]/a')

for cat in categories:
    category_name = cat.xpath('string(.)').get().strip()
    category_href = cat.xpath('./@href').get()
    category_url = urljoin(base_url, category_href)

    current_page_url = category_url
    page_count = 0
    category_urls = []

    while True:
        page_count += 1

        try:
            page_response = requests.get(current_page_url, headers=headers, timeout=10)
            page_sel = Selector(page_response.text)

            listing_links = page_sel.xpath('//div[contains(@class, "_list__")]/div/a/@href').getall()
            
            for link in listing_links:
                full_link = urljoin(base_url, link)
                if full_link not in all_urls:
                    category_urls.append(full_link)
            next_page = page_sel.xpath('//div[contains(@class, "_pagination__")]//a[not(contains(@class,"_active__"))]/@href').get()

            if not next_page:
                break
            
            current_page_url = urljoin(base_url, next_page)

        except Exception as e:
            break

# ====================== parser ====================================
for i, url in enumerate(all_urls, 1):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    sel = Selector(response.text)
    
    property_data = {}
    
    property_data['id'] = sel.xpath('//div[contains(@class, "_item___4Sv8")][span[contains(text(), "Ad number")]]/following-sibling::div//span/text()').get()
    property_data['reference_number'] = property_data['id']
    property_data['url'] = url
    property_data['category'] = sel.xpath('//div[contains(@class, "_auction__")]//h2/text()').get()
    property_data['category_url'] = url
    property_data['title'] = property_data['category']
    property_data['description'] = sel.xpath('//div[contains(@class, "_root__")]//p/text()').get()
    property_data['location'] = sel.xpath('//div[contains(@class, "_approvedPreciseLocation__")]//span/text()').get()
    property_data['price'] = sel.xpath('//h2[contains(@class, "_price__")]//span/text()').get()
    property_data['currency'] = 'SAR'
    property_data['bedrooms'] = sel.xpath('//div[contains(@class, "_item___4Sv8")][div[contains(text(), "bedrooms")]]/following-sibling::div/text()').get()
    property_data['bathrooms'] = None
    property_data['scraped_ts'] = datetime.datetime.now().isoformat()
    
    amenities = sel.xpath('//div[contains(@class, "_boolean__waHdB")]//font/text()').getall()
    property_data['amenities'] = ', '.join(amenities) if amenities else None
    property_data['agent_name'] = sel.xpath('//h2[contains(@class, "_name__")]/text()').get()
    property_data['number_of_photos'] = ""
    property_data['phone_number'] = ""   
    date_added = sel.xpath('//div[contains(@class, "_item___4Sv8")][span[contains(text(), "Date Added")]]/span/text()').get()
    property_data['property_type'] = property_data['category']
    property_data['published_at'] = date_added
    
#  ================== findings ====================================
"""
some of the fieds not availabe in html
"""