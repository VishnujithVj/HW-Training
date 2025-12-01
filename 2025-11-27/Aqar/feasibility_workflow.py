import re
import requests
from parsel import Selector
from urllib.parse import urljoin
from datetime import datetime, timezone
import time

"""------------------CONFIGURATION --------------------"""

BASE_URL = "https://sa.aqar.fm/"

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.9',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}

"""------------- CATEGORY & URL CRAWLER -------------------"""

def test_category():
    """Test: Extracting category URLs from homepage"""
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        sel = Selector(response.text)
        
        categories = sel.xpath('//div[contains(@class, "_list__")]/a')
        
        if not categories:
            return []
        
        category_urls = []
        for cat in categories:
            cat_name = cat.xpath('string(.)').get().strip()
            cat_href = cat.xpath('./@href').get()
            cat_url = urljoin(BASE_URL, cat_href).rstrip("/")
            
            category_urls.append({
                'name': cat_name,
                'url': cat_url
            })
        
        return category_urls
        
    except Exception as e:
        return []
    
def test_pagination(category_url, max_pages=3):
    """Test: pagination through a category and extract product URLs"""
    
    while page_num <= max_pages:
        page_url = f"{category_url}/{page_num}"
        
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=10)
            sel = Selector(response.text)           
            listings = sel.xpath('//div[contains(@class, "_list__")]/div/a/@href').getall()
            
            for link in listings:
                full_url = urljoin(BASE_URL, link)
            
            page_num += 1
            time.sleep(0.5)
            
        except Exception as e:
            break

    return 


"""------------- PRODUCT PARSER TEST -------------------"""

def clean_description(description):
    """Clean Arabic description text"""
    description = re.sub(r"المزيد$", "", description).strip()
    description = re.sub(r"\s*\n\s*", " ", description)
    description = re.sub(r"\s+", " ", description)
    description = re.sub(r"[^\w\s\u0600-\u06FF.,!?/:()\-]", "", description)
    return description.strip()

def test_product(product_url):
    """Test: Parse product details from a product page"""
    
    response = requests.get(product_url, headers=HEADERS, timeout=20)
    
    if response.status_code != 200:
        return None
    
    sel = Selector(response.text)
    html = response.text
    
    # XPATH EXTRACTION
    title = sel.xpath('//div[contains(@class,"_title")]//h1/text()').get() or ""
    
    desc_nodes = sel.xpath(
        '//div[contains(@class,"_card__nZw1i")]//div[contains(@class,"_root__lFkcr")]//text()'
    ).getall()
    raw_desc = " ".join([d.strip() for d in desc_nodes if d.strip()])
    description = clean_description(raw_desc)
    
    price = sel.xpath('//div[contains(@class,"_pricing")]//h2/span/text()').get()
    price = price.replace(",", "") if price else None
    
    bedrooms = sel.xpath('//*[contains(text(),"غرف النوم")]/following::div[1]//text()').get()
    
    published_at = sel.xpath(
        '//span[contains(text(),"تاريخ الإضافة")]/following-sibling::span/text()'
    ).get()
    
    category_raw = sel.xpath('//div[contains(@class,"_auction")]//h2/text()').get()
    
    number_of_photos = len(sel.xpath('//div[contains(@class,"_listingImages__tKNxb")]//img').getall())
    
    # REGEX EXTRACTION
    emp_match = re.search(
        r'"responsible_employee_name"\s*:\s*"([^"]+)"\s*,\s*"responsible_employee_phone_number"\s*:\s*"([^"]+)"',
        html
    )
    agent_name = emp_match.group(1) if emp_match else None
    phone_number = emp_match.group(2) if emp_match else None
    
    bathrooms_match = re.search(
        r'"name"\s*:\s*"عدد دورات المياه"\s*,\s*"value"\s*:\s*("?)(\d+)\1',
        html
    )
    bathrooms = bathrooms_match.group(2) if bathrooms_match else None
    
    loc_match = re.search(r'"streetAddress"\s*:\s*"([^"]+)"', html)
    location = loc_match.group(1).strip() if loc_match else None
    
    ref_match = re.search(r'\\"id\\"\s*:\s*(\d+)', html)
    reference = ref_match.group(1) if ref_match else None
    
    # DETAILS TABLE
    details = {}
    for box in sel.xpath('//div[contains(@class, "_newSpecCard")]//div[contains(@class, "_item___")]'):
        key = box.xpath('.//div[contains(@class,"_label")]/text()').get()
        value = box.xpath('.//div[contains(@class,"_value")]/text()').get()
        if key and value:
            details[key.strip()] = value.strip()
    
    # AMENITIES LIST
    amenities = []
    for a in sel.xpath('//div[contains(@class,"_boolean__")]/div[contains(@class,"_label")]'):
        txt = "".join(a.xpath('.//text()').getall()).strip()
        if txt:
            amenities.append(txt)
    
    # PROPERTY TYPE
    property_type = None
    arabic_map = {"للإيجار": "for rent", "للايجار": "for rent", "للبيع": "for sale"}
    if category_raw:
        cat_clean = category_raw.strip()
        for k, v in arabic_map.items():
            if k in cat_clean:
                property_type = v
    else:
        cat_clean = None
    
    # BUILD ITEM
    item = {
        "id": reference,
        "reference_number": reference,
        "url": product_url,
        "category": cat_clean,
        "title": title,
        "description": description,
        "location": location,
        "price": price,
        "currency": "SAR",
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "property_type": property_type,
        "published_at": published_at,
        "agent_name": agent_name,
        "phone_number": phone_number,
        "number_of_photos": number_of_photos,
        "amenities": amenities,
        "details": details,
        "scraped_ts": datetime.now(timezone.utc),
    }
    
    return item
    
""" ------------- FINDINGS -------------------""" 
