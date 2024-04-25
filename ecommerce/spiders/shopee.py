from ecommerce.spiders.base_spider import BaseSpider
from datetime import datetime
import requests
import scrapy
from urllib.parse import urlencode, quote
import demoji


class Spider(BaseSpider):
    name = 'shopee'
    start_urls = ['https://shopee.sg/']

    site_id = 11
    site_name = 'Shopee'
    site_url = 'https://shopee.sg'
    site_favicon = 'https://shopee.sg/favicon.ico'
    logo = 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Shopee.svg/1200px-Shopee.svg.png'

    def parse(self, response):
        products_url = "https://shopee.sg/api/v4/search/search_items"
        item_url = "https://shopee.sg/api/v4/item/get?"

        headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
                    "X-Requested-With": "XMLHttpRequest",
                    "If-None-Match-": "55b03-c627987a2d33ab84dec29c1611a0bcf5",
                }
        categories = {
            '11013350': ('https://shopee.sg/Mobile-Gadgets-cat.11013350', 'Mobile & Gadgets'),
            '11027421': ('https://shopee.sg/Home-Appliances-cat.11027421', 'Home Appliances'),
            '11011538': ('https://shopee.sg/Toys-Kids-Babies-cat.11011538', 'Toys, Kids & Babies'),
            '11013247': ('https://shopee.sg/Computers-Peripherals-cat.11013247', 'Computers & Peripherals'),
            '11013478': ('https://shopee.sg/Video-Games-cat.11013478', 'Video Games'),
            '11012018': ('https://shopee.sg/Sports-Outdoors-cat.11012018', 'Sports & Outdoors'),
            '11011760': ('https://shopee.sg/Hobbies-Books-cat.11011760', 'Hobbies & Books'),
            '11012515': ('https://shopee.sg/Watches-cat.11012515', 'Watches'),
            '11013548': ('https://shopee.sg/Cameras-Drones-cat.11013548', 'Cameras & Drones'),
        }

        for category in categories:
            n = '-100'
            scraped_ids = []
            while True:
                n = int(n) + 100
                querystring = {"by":"relevancy","limit":"100","match_id":category,"newest":str(n),"order":"desc","page_type":"search","scenario":"PAGE_OTHERS","version":"2"}
                jsonResponse = requests.request("GET", products_url, headers=headers, params=querystring).json()
                if len(jsonResponse['items']) == 0:
                    break
                for product in jsonResponse['items']:
                    external_category = categories[category][1]
                    external_name = product['item_basic']['name']
                    shopID = product["item_basic"]["shopid"]
                    external_id = product["item_basic"]["itemid"]
                    historical_sold = product['item_basic']['historical_sold']
                    external_link = 'https://shopee.sg/' + external_name.replace(' ', '-') + f'-i.{shopID}.{external_id}?position=0'
                    querystring2 = {"itemid":external_id,"shopid":shopID}
                    yield scrapy.Request(item_url + urlencode(querystring2), headers=headers, meta={'historical': historical_sold, 'cat': external_category, 'link': external_link, 'name': external_name, 'id': external_id}, callback=self.parse_product, dont_filter=True)

    def parse_product(self, response):
        jsonResponse2 = response.json()
        description = jsonResponse2['data']['description']
        brand = jsonResponse2['data']['brand']
        scraping_date = datetime.today()
        images = ['https://cf.shopee.sg/file/' + url + '_tn' for url in jsonResponse2['data']['images']]
        models = [{
                'external_id': model['promotionid'],
                'name': model['name'],
                'description': '',
                'price': model['price'] / 100000,
                } for model in jsonResponse2['data']['models']]

        yield {
            'external_category': response.meta['cat'],
            'external_link': quote(response.meta['link']),
            'external_name': response.meta['name'],
            'description': demoji.replace(description, ''),
            'brand': brand,
            'external_id': response.meta['id'],
            'scraping_date': scraping_date,
            'models': models,
            'images': images,
            'Sold': response.meta['historical']
        }
        print(response.meta['name'])
