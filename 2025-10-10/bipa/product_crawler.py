import requests
import logging
import time
from parsel import Selector
from items import ProductUrlItem, CategoryUrlItem
from settings import HEADERS, BASE_URL, PRODUCTS_PER_PAGE

class ProductCrawler:
    """Crawling Product URLs"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def start(self):
        """Start crawling products from categories"""
        categories = CategoryUrlItem.objects()
        logging.info(f"Found {categories.count()} categories to process")
        
        for i, category in enumerate(categories, 1):
            logging.info(f"[{i}/{categories.count()}] Processing: {category.name}")
            self.process_category(category)
            time.sleep(1)

    def process_category(self, category):
        """Process single category with pagination using offset"""
        page = 0
        seen_urls = set()
        has_more_products = True
        
        while has_more_products:
            offset = page * PRODUCTS_PER_PAGE
            paged_url = f"{category.url}?offset={offset}"
            
            try:
                response = self.session.get(paged_url)
                if response.status_code != 200:
                    logging.warning(f"Failed to fetch page {page + 1} for {category.name}")
                    break
                    
                product_urls = self.extract_product_urls(response.text)
                
                if not product_urls:
                    logging.info(f"No more products found for {category.name} at page {page + 1}")
                    has_more_products = False
                    break
                    
                new_urls = [url for url in product_urls if url not in seen_urls]
                
                if not new_urls:
                    logging.info(f"No new products found for {category.name} at page {page + 1}")
                    has_more_products = False
                    break
                    
                """Save new product URLs"""
                for url in new_urls:
                    product_item = ProductUrlItem(
                        url=url,
                        category_url=category.url
                    )
                    product_item.save()
                    seen_urls.add(url)
                
                logging.info(f"Category: {category.name} | Page {page + 1}: Saved {len(new_urls)} products (Offset: {offset})")
                page += 1
                time.sleep(0.5) 
                
            except Exception as e:
                logging.error(f"Error processing category {category.name} at page {page + 1}: {e}")
                break

        logging.info(f"Completed {category.name}: Found {len(seen_urls)} total products")

    def extract_product_urls(self, html_content):
        """Extract product URLs from HTML"""
        sel = Selector(html_content)
        product_links = sel.xpath('//a[contains(@href,"/p/")]/@href').getall()

        """Clean and format URLs"""
        clean_urls = []
        for link in product_links:
            if link and '/p/' in link:
                if link.startswith('/'):
                    clean_url = BASE_URL + link.split('?')[0]
                else:
                    clean_url = link.split('?')[0]
                
                if clean_url.startswith('http') and clean_url not in clean_urls:
                    clean_urls.append(clean_url)
            
        return list(set(clean_urls)) 

    def close(self):
        self.session.close()
        logging.info("Product crawler completed")


if __name__ == "__main__":
    crawler = ProductCrawler()
    crawler.start()
    crawler.close()