import re

from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class TheHourGlassScraper(BaseSpider):
	name = 'thehourglass'
	site_id = 22
	site_name = 'The Hour Glass'
	site_url = 'https://www.thehourglass.com/'
	site_favicon = 'https://da8t9y7300ntx.cloudfront.net/wp-content/themes/atlas/favicon/favicon-16x16.png'
	logo = 'https://da8t9y7300ntx.cloudfront.net/wp-content/40th/images/THG40_cropped_2048x.png'
	start_urls = ['https://www.thehourglass.com/brands/']
	start_urls = [
		'https://www.thehourglass.com/catalog/all-f-p-journe/',
		'https://www.thehourglass.com/catalog/all-girard-perregaux/',
		'https://www.thehourglass.com/catalog/all-grand-seiko/',
		'https://www.thehourglass.com/catalog/hublot/all-hublot/',
		'https://www.thehourglass.com/catalog/iwc-schaffhausen/all-iwc-schaffhausen/',
		'https://www.thehourglass.com/catalog/all-de-bethune/',
		'https://www.thehourglass.com/catalog/louis-erard/all-louis-erard/',
		'https://www.thehourglass.com/catalog/panerai/all-panerai/',
		'https://www.thehourglass.com/catalog/patek-philippe/all/',
		'https://www.thehourglass.com/catalog/bvlgari/all-bvlgari/',
		'https://www.thehourglass.com/catalog/urwerk/all-urwerk/',
		'https://www.thehourglass.com/catalog/ulysse-nardin/all-ulysse-nardin/',
		'https://www.thehourglass.com/catalog/tag-heuer/all-tag-heuer/',
		'https://www.thehourglass.com/catalog/sinn/all-sinn/',
		'https://www.thehourglass.com/catalog/rado/all-rado/',
		'https://www.thehourglass.com/catalog/tudor/in-store/'
	]

	def parse(self, response):
		link = response.url
		type_brand = False
		if 'tudor' in link:
			product_links = response.xpath('//div[contains(@class, "gx gpx")]/div/a[contains(@href, "product")]/@href').getall()
			type_brand = True
			next_link = response.xpath('//a[@class="next page-numbers"]/@href').get()
			if next_link:
				yield scrapy.Request(next_link, callback=self.parse)
		else:
			product_links = response.xpath('//div[@class="show-for-largeOFF"]/a/@href').getall()
		for product_link in product_links:
			yield scrapy.Request(product_link, callback=self.parse_product, meta={'type': type_brand})

	def parse_product(self, response):
		type_brand = response.meta['type']
		if type_brand:
			product_name = response.xpath('//html[@lang="en-SG"]/head/title/text()').get().split(' | ')[0]
			brand = response.xpath('//h2[@class="watch_brand is-up"]/text()').get()
			description = response.xpath('//div[@class="watch_disclaimer"]/text()').get().strip().rstrip()
			price = float(response.xpath('//p[@class="watch_price"]/text()').get().strip().rstrip().split(' ')[1].replace(',', '').replace('*', ''))
			thumb_image = response.xpath('//ul[@id="lightSlider"]/li[1]/@data-thumb').get()
			all_images = [thumb_image]
			images = response.xpath('//ul[@id="lightSlider"]/li/img/@src').getall()
			all_images.extend(images)
		else:
			brand = response.xpath('//p[@id="watch_brand"]/text()').get()
			product_name = response.xpath('//h5[@id="watch_name"]/text()').get()
			product_name = f'{brand} {product_name}'
			serial = response.xpath('//p[@data-class="prd-name"]/text()').get()
			if serial:
				product_name += f' {serial}'
			description = response.xpath('//div[@class="spec-short-desc"]/text()').get().strip().rstrip()
			try:
				price = float(response.xpath('//b[@id="watch_id"]/text()').get().strip().rstrip().split(' ')[1].replace(',', '').replace('*', ''))
			except:
				price = 0
			thumb_image = response.xpath('//ul[@id="imageGallery"]/li[1]/@data-thumb').get()
			all_images = [thumb_image]
			images = response.xpath('//ul[@id="imageGallery"]/li/@data-src').getall()
			all_images.extend(images)
		if description:
			description = re.sub(r'[\n\t]+', ' ', description).strip().rstrip()
		product_id = response.xpath('//link[@rel="shortlink"]/@href').get().split('=')[1]
		if thumb_image is None:
			thumb_image = response.xpath('//meta[@property="og:image"]/@content').get()
			all_images = [thumb_image]
		item = {
			'external_category': 'Watches',
			'external_link': response.url,
			'external_name': product_name,
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
		if price != 0:
			print(item)
			yield item
