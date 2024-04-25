from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class KbLuxuryScraper(BaseSpider):
	name = 'kbluxury'
	site_id = 17
	site_name = 'K.B. Luxury Watch & Jewellery'
	site_url = 'https://sgwatches.com.sg/'
	site_favicon = 'https://sgwatches.com.sg/wp-content/uploads/2019/09/favicon.png'
	logo = 'https://sgwatches.com.sg/wp-content/uploads/2019/09/sgwatches_logo@2x.png'
	start_urls = ['https://sgwatches.com.sg/watches/page/1']

	headers = {
		'authority': 'sgwatches.com.sg',
		'pragma': 'no-cache',
		'cache-control': 'no-cache',
		'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
		'sec-ch-ua-mobile': '?0',
		'upgrade-insecure-requests': '1',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
		'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
		'sec-fetch-site': 'none',
		'sec-fetch-mode': 'navigate',
		'sec-fetch-user': '?1',
		'sec-fetch-dest': 'document',
		'accept-language': 'en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7',
		'cookie': '_ga=GA1.3.694102976.1634142036; _gid=GA1.3.837203049.1634142036; _gat_gtag_UA_53769825_1=1',
	}

	page = 1

	def parse(self, response):
		links = response.xpath('//div[@class="product-wrap"]/a/@href').getall()
		for link in links:
			yield scrapy.Request(link, callback=self.parse_product, headers=self.headers)
		if links:
			self.page += 1
			yield scrapy.Request(f'https://sgwatches.com.sg/watches/page/{self.page}', callback=self.parse, headers=self.headers)

	def parse_product(self, response):
		product_name = response.xpath('//h1/text()').get()
		description = response.xpath('//meta[@property="og:description"]/@content').get()
		price = float(response.xpath('//span[@class="woocommerce-Price-amount amount"]/bdi/text()').get().replace(',', ''))
		product_id = response.xpath('//button[@name="add-to-cart"]/@value').get()
		thumb_image = response.xpath('//div[@class="woocommerce-product-gallery__image easyzoom"]/@data-thumb').get()
		all_images = [thumb_image]
		images = response.xpath('//div[@class="woocommerce-product-gallery__image easyzoom"]/a/@href').getall()
		all_images.extend(images)
		dsc = response.xpath('//span[@class="posted_in"]/a/text()').getall()
		brand = ''
		for ds in dsc:
			low = ds.lower()
			if 'rolex' in low:
				brand = 'Rolex'
				break
			elif 'panerai' in low:
				brand = 'Panerai'
				break
			elif 'tudor' in low:
				brand = 'Tudor'
				break
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
