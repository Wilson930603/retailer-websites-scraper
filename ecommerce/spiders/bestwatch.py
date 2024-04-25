from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class BestwatchScraper(BaseSpider):
	name = 'bestwatch'
	site_id = 16
	site_name = 'Best Watch'
	site_url = 'https://bestwatch.sg/'
	site_favicon = 'https://bestwatch.sg/media/favicon/stores/8/fav_1.png'
	logo = 'https://bestwatch.sg/static/version1636517475/frontend/BestWatch/default/en_US/images/logo.svg'

	def start_requests(self):
		page = 1
		yield scrapy.Request(f'https://bestwatch.sg/watches.html?p={page}', meta={'page': page}, callback=self.parse)

	def parse(self, response):
		products = response.xpath('//a[@class="type-name-new"]')
		for product in products:
			product_link = product.xpath('./@href').get()
			yield scrapy.Request(product_link, callback=self.parse_product)
		if products:
			page = response.meta['page'] + 1
			yield scrapy.Request(f'https://bestwatch.sg/watches.html?p={page}', meta={'page': page}, callback=self.parse, dont_filter=True)

	def parse_product(self, response):
		product_name = response.xpath('//span[@class="product-item-name"]/text()').get()
		price = response.xpath('//span[@data-price-type="finalPrice"]/@data-price-amount').get()
		product_id = response.xpath('//div[@data-role="priceBox"]/@data-product-id').get()
		description = response.xpath('//meta[@name="description"]/@content').get()
		brand = response.xpath('//div[@class="product-item-brand type-name-new"]/span/text()').get()
		thumb_image = response.xpath('(//a[@data-zoom-id="zoom"])[1]/img/@src').get()
		images = response.xpath('//a[@data-zoom-id="zoom"]/@href').getall()
		all_images = [thumb_image]
		all_images.extend(images)
		item = {
			'external_category': 'Watches',
			'external_link': response.url,
			'external_name': f'{brand} {product_name}',
			'description': description,
			'brand': brand,
			'external_id': product_id,
			'models': [
				{
					'external_id': product_id,
					'name': product_name,
					'price': float(price),
					'image': thumb_image
				}
			],
			'images': all_images
		}
		print(item)
		yield item
