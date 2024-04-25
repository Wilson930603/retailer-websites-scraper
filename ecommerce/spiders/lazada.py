import re

from ecommerce.spiders.base_spider import BaseSpider
import scrapy
from datetime import datetime


class LazadaScraper(BaseSpider):
	name = 'lazada'
	site_id = 5
	site_name = 'Lazada'
	site_url = 'https://www.lazada.sg/'
	site_favicon = 'https://laz-img-cdn.alicdn.com/tfs/TB1ODo.f2b2gK0jSZK9XXaEgFXa-64-64.png'
	logo = 'https://laz-img-cdn.alicdn.com/images/ims-web/TB12_ByawFY.1VjSZFnXXcFHXXa.png'
	start_urls = ['https://www.lazada.sg/']

	def parse(self, response):
		categories = [1, 2, 3, 5, 10]
		for category_id in categories:
			links = response.xpath(f'//ul[@class="lzd-site-menu-sub Level_1_Category_No{category_id}"]//li/a/@href').getall()
			for link in links:
				page = 1
				base_link = f'https:{link}?ajax=true&page='
				yield scrapy.Request(f'{base_link}{page}', meta={'base_link': base_link, 'page': page}, callback=self.parse_menu)

	def parse_menu(self, response):
		base_link = response.meta['base_link']
		page = response.meta['page']
		print(response.url)
		try:
			mods = response.json()['mods']
			cat_name = ''
			if 'resultTips' in mods:
				cat_name = mods['resultTips']['title']
			products = []
			if 'listItems' in mods:
				products = mods['listItems']
				for product in products:
					url = f'https:{product["productUrl"]}'
					desc = '\n'.join(product['description'])
					if desc:
						desc = re.sub(r'[\n\t]+', ' ', desc).strip().rstrip()
					item = {
						'external_category': cat_name,
						'external_link': url,
						'external_name': product['name'],
						'description': desc,
						'brand': product['brandName'],
						'external_id': product['itemId'],
						'scraping_date': '',
						'models': [],
						'images': []
					}
					yield scrapy.Request(url, callback=self.parse_product, meta={'item': item})
			if products:
				page += 1
				yield scrapy.Request(f'{base_link}{page}', meta={'base_link': base_link, 'page': page}, callback=self.parse_menu, dont_filter=True)
		except:
			yield scrapy.Request(f'{base_link}{page}', meta={'base_link': base_link, 'page': page}, callback=self.parse_menu, dont_filter=True)

	def parse_product(self, response):
		item = response.meta['item']
		data = eval(re.search('var __moduleData__.+', response.text)[0].replace('var __moduleData__ = ', '')[0:-1].replace('false', 'False').replace('true', 'True'))['data']['root']['fields']
		images = []
		sku_base = data['productOption']['skuBase']
		vid_names = {}
		for op in sku_base['properties']:
			for o in op['values']:
				vid_names[f'{op["pid"]}:{o["vid"]}'] = o['name']
		names = {}
		for option in sku_base['skus']:
			name = []
			options = option['propPath'].split(';')
			for key in options:
				name.append(vid_names[key])
			names[option['skuId']] = ' '.join(name)
		skus = data['primaryKey']['loadedSkuIds']
		variants = []
		sku_infos = data['skuInfos']
		for sku in skus:
			price = sku_infos[sku]['price']['salePrice']['text']
			if price:
				price = float(price.replace('$', '').replace(',', ''))
			obj = {
				'external_id': sku,
				'name': names[sku],
				'description': '',
				'price': price
			}
			variants.append(obj)
			for img in data['skuGalleries'][sku]:
				images.append(img['src'])
		for image in images:
			if image.startswith('//'):
				item['images'].append(f'https:{image}')
			else:
				item['images'].append(image)
		item['models'] = variants
		today = datetime.now()
		dt = today.strftime("%Y-%m-%d %H:%M:%S")
		item['scraping_date'] = dt
		print(item)
		yield item
