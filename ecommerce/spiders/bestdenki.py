from datetime import datetime

from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class BestDenkiScraper(BaseSpider):
	name = 'bestdenki'
	site_id = 3
	site_name = 'Best Denki'
	site_url = 'https://www.bestdenki.com.sg/'
	site_favicon = 'https://www.bestdenki.com.sg/pub/media/favicon/stores/1/favicon.png'
	logo = 'https://www.bestdenki.com.sg/pub/media/logo/stores/1/logo_1.png'

	def start_requests(self):
		categories = [
			{
				'cat': 'TV & Entertainment',
				'link': 'https://www.bestdenki.com.sg/tv-entertainment.html'
			},
			{
				'cat': 'IT & Mobile',
				'link': 'https://www.bestdenki.com.sg/it-mobile.html'
			},
			{
				'cat': 'Home Appliances',
				'link': 'https://www.bestdenki.com.sg/home-appliances.html'
			},
			{
				'cat': 'Kitchen Appliances',
				'link': 'https://www.bestdenki.com.sg/kitchen-cooking-appliances.html'
			},
			{
				'cat': 'Health & Beauty Care',
				'link': 'https://www.bestdenki.com.sg/fitness-personal-care.html'
			},
			{
				'cat': 'Fans & Air Care',
				'link': 'https://www.bestdenki.com.sg/aircon-air-care/fans-air-care.html'
			},
			{
				'cat': 'Air Conditioners',
				'link': 'https://www.bestdenki.com.sg/aircon-air-care/air-con.html'
			},
		]
		for category in categories:
			name = category['cat']
			link = category['link']
			final_link = f'{link}?product_list_limit=36'
			yield scrapy.Request(final_link, meta={'cat': name}, callback=self.parse_menu)

	def parse_menu(self, response):
		cat = response.meta['cat']
		product_links = response.xpath('//div[@class="column main col-lg-9 col-md-9 col-sm-12 col-xs-12 pull-right"]//a[@class="product-item-link"]/@href').getall()
		for product_link in product_links:
			yield scrapy.Request(product_link, meta={'cat': cat}, callback=self.parse_product)
		next_link = response.xpath('//a[@title="Next"]/@href').get()
		if next_link:
			yield scrapy.Request(next_link, meta={'cat': cat}, callback=self.parse_menu, dont_filter=True)

	def parse_product(self, response):
		cat = response.meta['cat']
		name = response.xpath('//h1[@class="product-name"]/text()').get().strip().rstrip()
		additional = response.xpath('//div[@class="webmodeldescription"]/text()').get()
		if additional:
			name = f'{name} {additional}'
		images = [response.xpath('//meta[@property="og:image"]/@content').get()]
		url = response.url
		price = float(response.xpath('//meta[@property="product:price:amount"]/@content').get())
		desc = response.xpath('//meta[@property="og:description"]/@content').get()
		brand = response.xpath('//div[@class="brand-name"]/a/@title').get()
		sku = response.xpath('//span[@itemprop="sku"]/text()').get()
		for img in response.xpath('//div[@class="product item-image imgzoom"]/@data-zoom').getall():
			if img not in images:
				images.append(img)
		today = datetime.now()
		dt = today.strftime("%Y-%m-%d %H:%M:%S")
		item = {
			'external_category': cat,
			'external_link': url,
			'external_name': name,
			'description': desc,
			'brand': brand,
			'external_id': sku,
			'scraping_date': dt,
			'models': [
				{
					'external_id': sku,
					'name': name,
					'description': '',
					'price': price
				}
			],
			'images': images
		}
		print(item)
		yield item
