from ecommerce.spiders.base_spider import BaseSpider
from datetime import datetime
import scrapy
import regex
import json
import string
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup


class Spider(BaseSpider):
    name = 'hachitech'
    params = {
        'x-algolia-agent': 'Algolia for JavaScript (4.10.5); Browser (lite); instantsearch.js (4.30.1); Vue (2.6.14); Vue InstantSearch (3.8.1); JS Helper (3.5.5)',
        'x-algolia-application-id': '6BC318IJNF',
        'x-algolia-api-key': '88c8a34f2b7653f93b1ce0053dbc64fe'
    }
    api_url = "https://6bc318ijnf-dsn.algolia.net/1/indexes/*/queries?"
    start_urls = ['https://www.hachi.tech/settings/menu']
    site_id = 9
    site_name = 'Hachi.tech'
    site_url = 'https://www.hachi.tech'
    site_favicon = 'https://www.hachi.tech/favicon.ico'
    logo = 'https://www.hachi.tech/img/logo-2107.png'

    def parse(self, response):
        for letter1 in string.ascii_lowercase:
            for letter2 in string.ascii_lowercase:
                alpha = letter1 + letter2
                data = {"requests":[{"indexName":"hachisearchengine","params":f'query={alpha}&hitsPerPage=1000'}]}
                yield scrapy.Request(self.api_url + urlencode(self.params), method='POST', meta={'d': alpha},body=json.dumps(data), callback=self.parse_json)

    scraped_ids = []
    def parse_json(self, response):
        jsonBody = response.json()
        
        try:
            products = jsonBody['results'][0]['hits']
        except:
            return
        for product in products:
            external_id = product['item_id']
            external_name = product['item_desc'].strip()
            if 'HSG' not in product['active_sites'] or external_id in self.scraped_ids or not external_name:
                continue
            self.scraped_ids.append(external_id)
            scraping_date = datetime.today()
            description = product['item_desc']
            images = [product['image_url']]
            
            try:
                external_category = product['boutiquecates'][0]['boutique']
            except:
                external_category = ''
            price = product['prices']['MEMBER'] if product['prices']['MEMBER'] else product['regular_price']
            external_link = f'https://www.hachi.tech/product/{external_id}'
            try:
                r2 = requests.get(f'{external_link}/descriptions')
                soup = BeautifulSoup(r2.json()['data']['OVERVIEW']['body'], 'lxml')
                description = soup.text.replace('\n', '')
            except:
                description = ''
            brand = product['brand_id']

            models_data = [{
                    'external_id': external_id,
                    'name': external_name,
                    'description': '',
                    'price': price
                    }]

            yield {
                'external_category': external_category,
                'external_link': external_link,
                'external_name': external_name,
                'description': description,
                'brand': brand,
                'external_id': external_id,
                'scraping_date': scraping_date,
                'models': models_data,
                'images': images
            }