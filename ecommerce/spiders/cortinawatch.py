from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class CortinaWatchScraper(BaseSpider):
	name = 'cortinawatch'
	site_id = 19
	site_name = 'Cortina Watch'
	site_url = 'https://www.cortinawatch.online/'
	site_favicon = 'https://www.cortinawatch.online/assets/frontend/images/favicon.png'
	start_urls = ['https://www.cortinawatch.online/products']
	logo = 'https://www.cortinawatch.online/assets/frontend/images/logo.png'

	def parse(self, response):
		links = response.xpath('//div[@class="products"]/a/@href').getall()
		for link in links:
			yield scrapy.Request(link, callback=self.parse_product)

	def parse_product(self, response):
		product_name = response.xpath('//div[@class="col-xs-12 col-sm-12 wrapdetails"]/h4/text()').get()
		brand = response.xpath('//div[@class="col-xs-12 col-sm-12 wrapdetails"]/h1/text()').get()
		product_name = f'{brand} {product_name}'
		model = response.xpath('//span[@class="model"]/text()').get()
		if model:
			model = model.split(' ', 1)[1]
			product_name += f' {model}'
		product_id = response.xpath('//ul[@class="col-xs-12 col-sm-12 wrapbtncart"]//a/@pcq_ref').get()
		description = response.xpath('//ul[@class="aboutlist"]/p/text()').get()
		price = float(response.xpath('//span[@class="estprice"]/text()').get().strip().rstrip().split(' ')[1].replace(',', ''))
		thumb_image = response.xpath('//meta[@name="og:image"]/@content').get()
		all_images = [thumb_image]
		images = response.xpath('//div[@class="main-product zoomHolder"]/img/@src').getall()
		all_images.extend(images)
		all_images = list(set(all_images))
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
		print(item)
		yield item
