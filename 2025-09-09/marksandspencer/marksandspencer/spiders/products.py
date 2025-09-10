import json
import re
import scrapy


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["marksandspencer.com"]
    start_urls = ["https://www.marksandspencer.com/"]

    def parse(self, response):
        category_links = response.xpath('//a[contains(@href, "/l/")]/@href').getall()
        for link in category_links:
            yield response.follow(link, callback=self.parse_category)

    def parse_category(self, response):
        product_links = response.xpath('//a[contains(@href,"/p/")]/@href').getall()
        for link in product_links:
            yield response.follow(link, callback=self.parse_product)

        next_page = response.xpath(
            '//a[contains(@class,"pagination-button--next") or contains(@data-test,"pagination-next")]/@href'
        ).get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_category)

    def parse_product(self, response):
        def clean_list(data):
            return [d.strip() for d in data if d and d.strip()]

        def clean_join(data):
            return " ".join([d.strip() for d in data if d and d.strip()])

        product_data = {}
        product_color = []
        for s in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(s)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    product_data = data
            
                    product_color = re.findall(r'"colour"\s*:\s*"([^"]+)"', s)
                    break
            except json.JSONDecodeError:
                continue

        product_id = response.xpath('//p[contains(@class,"media-0_textXs__ZzHWu")]/text()').getall()

        if not product_color:
            product_color = clean_list(
                response.xpath('//span[@class="media-0_textSm__Q52Mz"]/text()').getall()
            )

        yield {
            "unique_id": product_id[2] if len(product_id) > 2 else "",
            "product_name": product_data.get("name") or response.xpath('normalize-space(//h1/text())').get() or "",
            "brand": product_data.get("brand", {}).get("name") or "Marks & Spencer",
            "category": response.xpath('(//li[contains(@class,"breadcrumb_listItem")]/a)[last()]/text()').get() or "",
            "selling_price": product_data.get("offers", {}).get("price") or response.xpath('//p[contains(@class,"media-0_headingSm__aysOm")]/text()').get() or "",
            "breadcrumb": " > ".join(clean_list(response.xpath('//li[contains(@class,"breadcrumb_listItem")]/a/text()').getall())),
            "pdp_url": response.url,
            "product_description": product_data.get("description") or clean_join(response.xpath('//div[contains(@class,"product-description")]//text()').getall()) or response.xpath('//meta[@name="description"]/@content').get() or "",
            "currency": product_data.get("offers", {}).get("priceCurrency") or "£",
            "color": product_color[7] if len(product_color) > 7 else "",
            "size": clean_list(response.xpath('//span[contains(@class,"media-0_body__yf6Z_ selector_unavailableText__06teW")]/text()').getall()) or [""],
            "rating": response.xpath('//div[contains(@class,"star-rating")]/@aria-label').get() or response.xpath('//span[contains(@class,"star-rating")]//text()').get() or "",
            "review": product_data.get("aggregateRating", {}).get("reviewCount") or response.xpath('//span[contains(@class,"review")]/text()').get() or "",
            "material_composition": clean_join(response.xpath('//div[contains(@class,"composition")]//text()').getall()) or "",
            "style": response.xpath('//p[contains(text(),"Style")]/following-sibling::p/text()').get() or "",
            "care_instructions": clean_join(response.xpath('//p[contains(@class,"product-details_careText__t_RPG")]/text()').getall()) or "",
            "images": product_data.get("image", []) or clean_list(response.xpath('//img[contains(@class,"product-image-hover_primary")]/@srcset').getall()),
        }
