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

        # Extract PDP links
        product_links = response.xpath('//a[contains(@href,"/p/")]/@href').getall()
        for link in product_links:
            yield response.follow(link, callback=self.parse_product)

        # Handle pagination
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
        productcode = response.xpath('//p[@class="media-0_textXs__ZzHWu"]/text()').get()
        yield {
            "unique_id": productcode,
            "product_name": response.xpath('normalize-space(//h1/text())').get(),
            "brand": "Marks & Spencer",
            "category": response.xpath('(//li[contains(@class,"breadcrumb_listItem")]/a)[last()]/text()').get(),
            "regular_price": response.xpath('normalize-space(//span[contains(@class,"price--rrp")]/text())').get(),
            "selling_price": response.xpath('//p[contains(@class,"headingSm")]/text()').get(),
            "promotion_description": response.xpath('normalize-space(//span[contains(@class,"promotion")]/text())').get(),
            "breadcrumb": " > ".join(clean_list(response.xpath('//li[contains(@class,"breadcrumb_listItem")]/a/text()').getall())),
            "pdp_url": response.url,
            "product_description": clean_join(response.xpath('//div[contains(@class,"product-description")]//text()').getall()),
            "currency": "£",
            "color": clean_list(response.xpath('//span[contains(@class,"swatch")]//text()').getall()),
            "size": clean_list(response.xpath('//span[contains(@class,"size")]/text()').getall()),
            "rating": response.xpath('normalize-space(//span[contains(@class,"star-rating")]/text())').get(),
            "review": response.xpath('normalize-space(//span[contains(@class,"review")]/text())').get(),
            "material_composition": clean_join(response.xpath('//div[contains(@class,"composition")]//text()').getall()),
            "style": response.xpath('normalize-space(//p[contains(text(),"Style")]/following-sibling::p/text())').get(),
            "care_instructions": response.xpath('normalize-space(//p[contains(text(),"Care")]/following-sibling::p/text())').get(),
            "feature": clean_list(response.xpath('//ul[contains(@class,"productFeatures")]//li/text()').getall()),
            "images": clean_list([img.split(",")[-1].strip().split(" ")[0] for img in response.xpath('//img[contains(@class,"product-image-hover_primary")]/@srcset').getall()]),
        }
