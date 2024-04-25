import re

from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class AmazonScraper(BaseSpider):
	name = 'amazon'
	site_id = 2
	site_name = 'Amazon'
	site_url = 'https://www.amazon.sg/'
	site_favicon = 'https://www.amazon.sg/favicon.ico'
	logo = 'https://photos.prnasia.com/media_files/static/2020/01/thumbs/202001101256_7132581d_2.jpg'
	headers = {
		'authority': 'www.amazon.sg',
		'pragma': 'no-cache',
		'cache-control': 'no-cache',
		'rtt': '100',
		'downlink': '9.35',
		'ect': '4g',
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
	}

	def start_requests(self):
		categories = ['6314449051', '6314388051', '6314630051', '6315182051', '6436071051', '6436069051', '6314572051', '6314273051']
		for category_id in categories:
			yield scrapy.Request(f'https://www.amazon.sg/s?rh=n%3A{category_id}&fs=true', dont_filter=True, callback=self.parse_menu, headers=self.headers)

	def parse_menu(self, response):
		cat_name = response.xpath('//select[@id="searchDropdownBox"]/option[@selected]/text()').get()
		links = response.xpath('//a[@class="a-link-normal a-text-normal"]')
		for link in links:
			name = link.xpath('./span/text()').get()
			link_path = link.xpath('./@href').get()
			final_link = f'https://www.amazon.sg{link_path}'
			yield scrapy.Request(final_link, callback=self.parse_product, meta={'cat_name': cat_name, 'name': name}, headers=self.headers)
		next_page = response.xpath('//li[@class="a-last"]/a/@href').get()
		if next_page:
			yield scrapy.Request(f'https://www.amazon.sg{next_page}', dont_filter=True, callback=self.parse_menu, headers=self.headers)

	def parse_product(self, response):
		cat_name = response.meta['cat_name']
		prod_name = response.meta['name']
		desc = ' '.join(response.xpath('//div[@id="feature-bullets"]/ul/li/span/text()').getall())
		if desc:
			desc = re.sub(r'[\n\t ]+', ' ', desc).strip().rstrip()
		data = eval(re.search('var obj = jQuery.+', response.text)[0].split("'", 1)[1].rsplit("'", 1)[0].replace('false', 'False').replace('true', 'True').replace('null', 'None'))
		product_id = data['parentAsin']
		brand = response.xpath('//a[@id="bylineInfo"]/text()').get()
		item = {
			'external_category': cat_name,
			'external_link': response.url,
			'external_name': prod_name,
			'description': desc,
			'brand': brand,
			'external_id': product_id,
			'scraping_date': '',
			'models': [],
			'images': []
		}
		images = []
		img = response.xpath('//ul[@class="a-unordered-list a-nostyle a-horizontal list maintain-height"]//img/@src').get()
		images.append(img)
		try:
			base_json_images = eval(re.search("'colorImages':.+", response.text)[0].split(': ', 1)[1][0:-1].replace('false', 'False').replace('true', 'True').replace('null', 'None'))['initial']
		except:
			base_json_images = []
		for img in base_json_images:
			if 'hiRes' in img:
				path = img['hiRes']
			else:
				path = img['large']
			if path not in images:
				images.append(path)
		for color in data['colorImages']:
			for img in data['colorImages'][color]:
				if 'hiRes' in img:
					path = img['hiRes']
				else:
					path = img['large']
				if path not in images:
					images.append(path)
		for img in images:
			if img:
				item['images'].append(img)
		base_url = response.url.split('/dp/')[0]
		variation_ids = response.xpath('//li[@data-defaultasin and (contains(@id, "style_name_") or contains(@id, "size_name_"))]/@data-defaultasin').getall()
		if not variation_ids:
			links = response.xpath('//li//span[contains(@id, "a-autoid-")]/span/a/@href').getall()
			variation_ids = [link.split('/dp/')[1].split('/')[0] for link in links]
		if not variation_ids:
			variation_ids = [product_id]
		first_id = variation_ids.pop(0)
		yield scrapy.Request(f'{base_url}/dp/{first_id}', callback=self.parse_colors, meta={'item': item, 'var_ids': variation_ids, 'base_url': base_url, 'id_cur': first_id}, headers=self.headers)

	def parse_colors(self, response):
		cur_id = response.meta['id_cur']
		item = response.meta['item']
		var_ids = response.meta['var_ids']
		base_url = response.meta['base_url']
		color_ids = response.xpath('//li[@data-defaultasin and contains(@id, "color_name_")]/@data-defaultasin').getall()
		if not color_ids:
			color_ids = [cur_id]
		first_id = color_ids.pop(0)
		yield scrapy.Request(f'https://www.amazon.sg/gp/aod/ajax?asin={first_id}', meta={'item': item, 'var_ids': var_ids, 'base_url': base_url, 'id_cur': first_id, 'color_ids': color_ids}, headers=self.headers, callback=self.parse_price)

	def parse_price(self, response):
		cur_id = response.meta['id_cur']
		item = response.meta['item']
		var_ids = response.meta['var_ids']
		base_url = response.meta['base_url']
		color_ids = response.meta['color_ids']

		name = response.xpath('//h5[@id="aod-asin-title-text"]/text()').get().strip().rstrip()
		price = response.xpath('//span[@class="a-offscreen"]/text()').get()
		if price:
			price = float(price.replace(',', '').split('$')[1])

		model = {
			'external_id': cur_id,
			'name': name,
			'description': '',
			'price': price
		}
		item['models'].append(model)

		if color_ids:
			first_id = color_ids.pop(0)
			yield scrapy.Request(f'https://www.amazon.sg/gp/aod/ajax?asin={first_id}', meta={'item': item, 'var_ids': var_ids, 'base_url': base_url, 'id_cur': first_id, 'color_ids': color_ids}, headers=self.headers, callback=self.parse_price)
		elif var_ids:
			first_id = var_ids.pop(0)
			yield scrapy.Request(f'{base_url}/dp/{first_id}', callback=self.parse_colors,  meta={'item': item, 'var_ids': var_ids, 'base_url': base_url, 'id_cur': first_id}, headers=self.headers)
		else:
			print(item)
			yield item
