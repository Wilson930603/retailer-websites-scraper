from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class ChuanWatchScraper(BaseSpider):
	name = 'chuanwatch'
	site_id = 20
	site_name = 'Chuan Watch Singapore'
	site_url = 'https://chuanwatch.com/'
	site_favicon = 'https://chuanwatch.com/favicon.ico'
	logo = 'https://chuanwatch.com/images/logo.jpg'

	def start_requests(self):
		data = {
			'sortBy': 'latest',
			'displayNo': '0',
			'pageValue': '1'
		}
		yield scrapy.FormRequest('https://chuanwatch.com/view/watches.html', formdata=data, callback=self.parse)

	def parse(self, response):
		links = response.xpath('//div[@id="productWrapper"]/div/div/a/@href').getall()
		for link in links:
			new_link = link.replace('../products', 'https://chuanwatch.com/products')
			print(new_link)
			yield scrapy.Request(new_link, callback=self.parse_product)

	def parse_product(self, response):
		product_name = response.xpath('//div[@id="mainContent"]/h1/text()').get()
		brand = response.xpath('//div[@id="mainContent"]/h4/text()').get().split(' - > ', 1)[0]
		if ' | ' in brand:
			brand = brand.split(' | ')[0]
		product_id = response.url.split('products/')[1].split('-', 1)[0]
		try:
			price = float(response.xpath('//span[@class="productPrice"]/text()').get().split('$')[1].replace(',', ''))
		except:
			price = 0
		thumb_image = response.xpath('//div[@id="gal1"]/a[1]/img/@src').get().replace('../', 'https://chuanwatch.com/')
		all_images = [thumb_image]
		images = response.xpath('//div[@id="gal1"]/a/@data-image').getall()
		for img in images:
			img = img.replace('../', 'https://chuanwatch.com/')
			all_images.append(img)
		description = " ".join(response.xpath('//h4/table//td//text()').getall())
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
