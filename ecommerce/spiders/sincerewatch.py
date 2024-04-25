from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class SincereWatchScraper(BaseSpider):
	name = 'sincerewatch'
	site_id = 21
	site_name = 'Sincere Watch'
	site_url = 'https://sincerewatch.com/'
	site_favicon = 'https://corsivacdnsea.blob.core.windows.net/sincerewatchcdn/2020/12/favicon.png'
	logo = 'https://corsivacdncontent.blob.core.windows.net/sincerewatch/Sincerewatch-logo-final-black.svg'
	start_urls = ['https://sincerewatch.com/brand/watches/page/1/']

	def parse(self, response):
		links = response.xpath('//a[@class="woocommerce-LoopProduct-link woocommerce-loop-product__link"]/@href').getall()
		for link in links:
			yield scrapy.Request(link, callback=self.parse_product)
		next_page = response.xpath('//link[@rel="next"]/@href').get()
		if next_page:
			yield scrapy.Request(next_page, callback=self.parse)

	def parse_product(self, response):
		if 'tudor' in response.url:
			brand = response.xpath('//p[@class="cat"]/text()').get().strip().rstrip()
			product_name = response.xpath('//meta[@property="og:title"]/@content').get().split(' | ')[0]
			model = response.xpath('//div[@class="model"]/text()').get().strip().rstrip()
			product_name = f'{brand} {product_name} {model}'
			description = response.xpath('//div[@class="description mt-60"]/text()').get().strip().rstrip()
			price = float(response.xpath('//div[@class="price mt-40"]/span[@class="woocommerce-Price-amount amount"]/bdi/text()').get().replace(',', ''))
			thumb_image = response.xpath('(//div[@class="thumb-image"])[1]/img/@srcset').get().split(' ')[-2]
			images = response.xpath('//div[@class="thumb-image"]/img/@src').getall()
		else:
			product_name = " ".join(response.xpath('//p[@class="product-reference"]/text()').getall()).strip().rstrip()
			brand = response.xpath('//div[@class="brand"]/text()[1]').get().strip().rstrip()
			collection_name = response.xpath('//p[@class="collection-name"]/text()').get()
			if collection_name.lower() not in product_name.lower():
				product_name = f'{collection_name} {product_name}'
			if brand.lower() not in product_name.lower():
				product_name = f'{brand} {product_name}'
			description = response.xpath('//div[@id="nav-tabContent"]/div[1]/div[1]/div[1]/text()').get().strip().rstrip()
			price = float(response.xpath('//section[@class="container-fluid mg-50-100"]//p[@class="sub-price"]/text()[1]').get().strip().rstrip().split(' ')[1].replace(',', ''))
			thumb_image = response.xpath('//meta[@property="og:image"][2]/@content').get()
			images = response.xpath('//div[@class="swiper-wrapper"]/div/img/@src').getall()
		product_id = response.xpath('//link[@rel="shortlink"]/@href').get().split('=')[1]
		all_images = [thumb_image]
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
		if price != 0:
			print(item)
			yield item
