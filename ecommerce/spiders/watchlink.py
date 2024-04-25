from ecommerce.spiders.base_spider import BaseSpider
import scrapy


class WatchLinkScraper(BaseSpider):
	name = 'watchlink'
	site_id = 18
	site_name = 'Watchlink'
	site_url = 'https://www.watchlink.sg/'
	site_favicon = 'https://www.watchlink.sg/images/favicon.ico'
	logo = 'https://www.watchlink.sg/images/WatchlinkLogo-footer.png'

	def start_requests(self):
		index = 0
		base_link = 'https://www.watchlink.sg/Product/GetProducts?LastId=&BrandIdStr=&ConditionId=&SortById=6&ShownProdCount={}&PageSize=100&SearchQuery=&ProductStatusId=&BrandTypeId=&membersOnlyId=0'
		yield scrapy.Request(base_link.format(index), meta={'base_link': base_link, 'index': index}, callback=self.parse)

	def parse(self, response):
		base_link = response.meta["base_link"]
		index = response.meta["index"] + 100
		product_links = response.xpath('//a/@href').getall()
		for link in product_links:
			yield scrapy.Request(f'https://www.watchlink.sg{link}', callback=self.parse_product)
		if product_links:
			yield scrapy.Request(base_link.format(index), meta={'base_link': base_link, 'index': index}, callback=self.parse, dont_filter=True)

	def parse_product(self, response):
		product_name = response.xpath('//div[@class="row hide"]/div/h4/b/text()').get()
		description = response.xpath('//meta[@property="og:description"]/@content').get()
		thumb_image = response.xpath('//ul[@id="image-gallery"]/li/@data-thumb').get()
		all_images = [thumb_image]
		brand = response.xpath('//div[@class="productBrand"]/text()').get()
		price = float(response.xpath('//div[@class="product-detail-top"]/h3[contains(@style, "color:")]/text()').get().replace('&nbsp;', '').replace('SGD', '').replace(',', ''))
		images = response.xpath('//ul[@id="image-gallery"]/li/img[1]/@src').getall()
		all_images.extend(images)
		product_id = response.url.split('Details/')[1].split('/')[0]
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
