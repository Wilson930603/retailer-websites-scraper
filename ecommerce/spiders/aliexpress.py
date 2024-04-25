from datetime import datetime

from ecommerce.spiders.base_spider import BaseSpider
import scrapy
import re


class AliExpressScraper(BaseSpider):
	name = 'aliexpress'
	site_id = 1
	site_name = 'AliExpress'
	site_url = 'https://www.aliexpress.com/'
	site_favicon = 'https://ae01.alicdn.com/images/eng/wholesale/icon/aliexpress.ico'
	logo = 'https://ae01.alicdn.com/kf/H1674ac74299a489f8e2995c8b73006ceJ.png'
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-GB,en;q=0.5',
		'Connection': 'keep-alive',
		'Upgrade-Insecure-Requests': '1',
		'Sec-Fetch-Dest': 'document',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-site',
		'Sec-Fetch-User': '?1',
		'Cache-Control': 'max-age=0',
		'TE': 'trailers',
	}

	cookies = {
		'aep_usuc_f': 'site=glo&c_tp=SGD&region=SG&b_locale=en_US'
	}

	def start_requests(self):
		categories = [
			{
				'name': 'Phones & Telecommunications',
				'urls': [
					{'id': 509, 'slug': 'cellphones-telecommunications'}
				]
			},
			{
				'name': 'Computer, Office & Security',
				'urls': [
					{'id': 7, 'slug': 'computer-office'},
					{'id': 21, 'slug': 'education-office-supplies'},
					{'id': 30, 'slug': 'security-protection'}
				]
			},
			{
				'name': 'Consumer Electronics',
				'urls': [
					{'id': 44, 'slug': 'consumer-electronics'}
				]
			},
			{
				'name': 'Jewelry',
				'urls': [
					{'id': 1509, 'slug': 'jewelry-accessories'},
				]
			},
			{
				'name': 'Watches',
				'urls': [
					{'id': 1511, 'slug': 'watches'}
				]
			},
			{
				'name': 'Home, Pet & Appliances',
				'urls': [
					{'id': 15, 'slug': 'home-garden'},
					{'id': 100006206, 'slug': 'pet-products'},
					{'id': 6, 'slug': 'home-appliances'}
				]
			},
			{
				'name': 'Toys, Kids & Babies',
				'urls': [
					{'id': 26, 'slug': 'toys-hobbies'},
					{'id': 1501, 'slug': 'mother-kids'}
				]
			},
			{
				'name': 'Outdoor Fun & Sports',
				'urls': [
					{'id': 18, 'slug': 'sports-entertainment'}
				]
			},
		]
		for category in categories:
			for url in category['urls']:
				base_path = f'https://www.aliexpress.com/category/{url["id"]}/{url["slug"]}.html'
				page = 1
				yield scrapy.Request(f'{base_path}?page={page}', callback=self.parse, headers=self.headers, meta={'cat': category['name'], 'base_path': base_path, 'page': page}, cookies=self.cookies)

	def parse(self, response):
		cat = response.meta['cat']
		base_path = response.meta['base_path']
		page = response.meta['page']
		res = re.search('window.runParams = {"mods.+', response.text)
		if not res:
			yield scrapy.Request(response.url, callback=self.parse, headers=self.headers, dont_filter=True, meta={'cat': cat, 'base_path': base_path, 'page': page}, cookies=self.cookies)
		else:
			products = eval(res[0].split(' = ', 1)[1][0:-1].replace('true', 'True').replace('false', 'False'))['mods']['itemList']['content']
			for product in products:
				product_id = product['productId']
				yield scrapy.Request(f'https://www.aliexpress.com/item/{product_id}.html', headers=self.headers, callback=self.parse_product, meta={'cat': cat}, cookies=self.cookies)
			if products:
				page += 1
				yield scrapy.Request(f'{base_path}?page={page}', callback=self.parse, headers=self.headers, dont_filter=True, meta={'cat': cat, 'base_path': base_path, 'page': page}, cookies=self.cookies)

	def parse_product(self, response):
		cat = response.meta['cat']
		res = eval(re.search('data: .+', response.text)[0].split('data: ')[1][0:-1].replace('true', 'True').replace('false', 'False'))
		title_name = res['titleModule']['subject']
		brand = ''
		for prop in res['specsModule']['props']:
			if prop['attrName'] == 'Brand Name':
				brand = prop['attrValue']
				break
		sku = res['descriptionModule']['productId']
		idfs = {}
		for property in res['skuModule']['productSKUPropertyList']:
			for value in property['skuPropertyValues']:
				idfs[str(value['propertyValueId'])] = value['propertyValueDisplayName']
		models = []
		for model in res['skuModule']['skuPriceList']:
			name = []
			for i in model['skuPropIds'].split(','):
				name.append(idfs[i])
			name = ' - '.join(name)
			price = float(model['skuVal']['actSkuMultiCurrencyCalPrice'])
			m = {
				'external_id': model['skuIdStr'],
				'name': name,
				'description': '',
				'price': price
			}
			models.append(m)
		images = []
		try:
			images = [res['imageModule']['summImagePathList'][0]]
		except:
			pass
		images.extend(res['imageModule']['imagePathList'])
		item = {
			'external_category': cat,
			'external_link': response.url,
			'external_name': title_name,
			'description': '',
			'brand': brand,
			'external_id': sku,
			'scraping_date': '',
			'models': models,
			'images': images
		}
		desc_link = res['descriptionModule']['descriptionUrl']
		yield scrapy.Request(desc_link, headers=self.headers, callback=self.parse_description, meta={'item': item}, cookies=self.cookies)

	def parse_description(self, response):
		item = response.meta['item']
		cleanr = re.compile('<.*?>')
		desc = re.sub(cleanr, '', response.text)
		desc = re.sub('window.adminAccountId=[0-9]+;', '', desc)
		desc = re.sub('[\n\t\r ]+', ' ', desc)
		item['description'] = desc
		today = datetime.now()
		dt = today.strftime("%Y-%m-%d %H:%M:%S")
		item['scraping_date'] = dt
		print(item)
		yield item
