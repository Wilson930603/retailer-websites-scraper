from ecommerce.spiders.base_spider import BaseSpider


class TestSpider(BaseSpider):
	name = 'test_proxy'
	start_urls = []

	def __init__(self):
		for i in range(10):
			self.start_urls.append(f'http://ident.me/{i}')

	def parse(self, response):
		print(f"RESPONSE:", response.text)
