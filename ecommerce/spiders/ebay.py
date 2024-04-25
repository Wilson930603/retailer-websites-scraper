from datetime import datetime

from ecommerce.spiders.base_spider import BaseSpider
import scrapy
import re


class EbayScraper(BaseSpider):
	name = 'ebay'

	site_id = 4
	site_name = 'Ebay'
	site_url = 'https://www.ebay.com.sg/'
	site_favicon = 'https://www.ebay.com.sg/favicon.ico'
	logo = 'https://logos-world.net/wp-content/uploads/2020/11/eBay-Logo-700x394.png'

	def start_requests(self):
		categories = ['267', '281', '293', '625', '1249', '11232', '11233', '15032', '58058']
		for category_id in categories:
			yield scrapy.Request(f'https://www.ebay.com.sg/b/{category_id}', callback=self.parse_menu, meta={"cat_id": category_id})

	def parse_menu(self, response):
		print(response.url)
		cat_id = response.meta['cat_id']
		cat_name = response.xpath(f'//option[@value="{cat_id}"]/text()').get().strip().rstrip()
		links = response.xpath('//li[@class="s-item s-item--large s-item--bgcolored"]//a[@class="s-item__link"]/@href').getall()
		for link in links:
			yield scrapy.Request(link, callback=self.parse_product, meta={'cat_name': cat_name})
		next_page = response.xpath('//a[@aria-label="Go to next search page"]/@href').get()
		if next_page:
			yield scrapy.Request(next_page, callback=self.parse_menu, dont_filter=True, meta={"cat_id": cat_id})

	def parse_product(self, response):
		condition = response.xpath('//div[@id="vi-itm-cond"]/text()').get()
		if 'new' in condition.lower():
			name = ' '.join(response.xpath('//h1[@id="itemTitle"]/text()').getall())
			price = response.xpath('//span[@id="convbinPrice"]/text()').get()
			if not price:
				price = response.xpath('//span[@id="convbidPrice"]/text()').get()
				if not price:
					price = response.xpath('//span[@id="prcIsum"]/text()').get()
			if price:
				price = float(price.replace(',','').rsplit(' ', 1)[1])
			product_id = response.xpath('//div[@id="descItemNumber"]/text()').get()
			brand = ''
			tds = response.xpath('//div[@class="itemAttr"]/div/table/tr/td')
			take = False
			for td in tds:
				if take:
					brand = td.xpath('./span/text()').get()
					break
				txt = ''
				try:
					txt = td.xpath('./text()').get().strip().rstrip()
				except:
					pass
				if txt == 'Brand:':
					take = True
			img = response.xpath('//img[@id="icImg"]/@src').get()
			images = [img]
			list_images = response.xpath('(//ul[@class="lst icon"])[2]//img/@src').getall()
			images.extend(list_images)
			item = {
				'external_category': response.meta['cat_name'],
				'external_link': response.url,
				'external_name': name,
				'description': '',
				'brand': brand,
				'external_id': product_id,
				'scraping_date': '',
				'models': [],
				'images': images
			}
			models = []
			try:
				json_data = eval(re.search("raptor\.require\('com\.ebay\.raptor\.vi\.cookie.+", response.text)[0].split("['com.ebay.raptor.vi.msku.ItemVariations','")[1].split("',", 1)[1].split("],['com.ebay.raptor.vi.isum.smartBackTo'")[0].replace('false', 'False').replace('true', 'True').replace('null', 'None'))['itmVarModel']
				sku_data = json_data['menuItemMap']
				price_data = json_data['itemVariationsMap']
				all_skus = {}
				for sku_ind in sku_data:
					sku_item = sku_data[str(sku_ind)]
					display_name = sku_item['displayName']
					sku_id = str(sku_item["matchingVariationIds"][0])
					all_skus[sku_id] = display_name
				for sku_id in price_data:
					price_item = price_data[sku_id]
					sku_price = price_item['priceAmountValue']['value']
					model = {
						'external_id': sku_id,
						'name': all_skus[sku_id],
						'description': '',
						'price': sku_price
					}
					models.append(model)
			except:
				pass
			if not models:
				models = [
					{
						'external_id': product_id,
						'name': name,
						'description': '',
						'price': price
					}
				]
			item['models'] = models
			yield scrapy.Request(f'https://vi.vipr.ebaydesc.com/ws/eBayISAPI.dll?item={product_id}', meta={'item': item}, callback=self.parse_description)

	def parse_description(self, response):
		item = response.meta['item']
		desc = ''
		lines = response.xpath('//div[@id="ds_div"]//text()').getall()
		for line in lines:
			line = line.strip().rstrip()
			if "@" in line or "{" in line:
				continue
			desc = f'{line}\n'
		if desc:
			desc = re.sub(r'[\n\t]+', ' ', desc).strip().rstrip()
		item['description'] = desc
		today = datetime.now()
		dt = today.strftime("%Y-%m-%d %H:%M:%S")
		item['scraping_date'] = dt
		print(item)
		yield item
