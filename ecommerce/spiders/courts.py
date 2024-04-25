from ecommerce.spiders.base_spider import BaseSpider
from datetime import datetime
import scrapy
import regex
import json
from urllib.parse import unquote
import random
from scrapy.utils.project import get_project_settings
import requests
from bs4 import BeautifulSoup
from threading import Thread
settings = get_project_settings()
proxies = open(settings.get('ROTATING_PROXY_LIST_PATH')).read().split('\n')


class Spider(BaseSpider):
    name = 'courts'
    start_urls = ['https://www.courts.com.sg/']

    site_id = 7
    site_name = 'Courts'
    site_url = 'https://www.courts.com.sg'
    site_favicon = 'https://www.courts.com.sg/media/favicon/stores/1/favicon.1.11_1.png'
    logo = 'https://www.courts.com.sg/media/logo/stores/1/courts-logo.1.11.png'

    scraped = []
    next = True
    def parse(self, response):
        sub_categories = []
        sub_categories = set(response.xpath('//a[@class="shop-all-button"]/@href').getall())
        sub_categories.remove('/articles')
        for subcat in sub_categories:
            yield scrapy.Request(f'https://www.courts.com.sg{subcat}?p=1&product_list_limit=32', callback=self.parse_category, dont_filter=True)
                
    threads = []
    threadResults = []
    def parse_category(self, response):
        product_links = response.xpath('//div[@class="product-item-info"]/a/@href').getall()
        for product in product_links:
            while True:
                proxy = random.choice(proxies)
                try:
                    if 'courts.com' not in product:
                        product = 'https://www.courts.com.sg/' + product
                    r = requests.get(product, proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'}, timeout=15)
                    break
                except Exception as err:
                    print(err)
                    continue
            t = Thread(target=self.parse_product, args=(r,))
            t.start()
            self.threads.append(t)
            if len(self.threads) > 30:
                for thread in self.threads:
                    thread.join()
                for data in self.threadResults:
                    if data['external_id'] in self.scraped:
                        continue
                    else:
                        self.scraped.append(data['external_id'])
                        yield data
                self.threads = []
                self.threadResults = []
        for thread in self.threads:
            thread.join()
        for data in self.threadResults:
            if data['external_id'] in self.scraped:
                  continue
            else:
                self.scraped.append(data['external_id'])
                yield data
        self.threads = []
        self.threadResults = []


        if response.xpath('//li[@class="item pages-item-next"]'):
            url = response.xpath('//li[@class="item pages-item-next"]/a/@href').get()
            if 'courts.com' not in url:
                url = 'https://www.courts.com.sg/' + url
            yield scrapy.Request(f'{url}&product_list_limit=32', callback=self.parse_category, dont_filter=True)

    def parse_product(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            external_id = soup.find('div', class_='price-box price-final_price')['data-product-id']
        except:
            return
        scraping_date = datetime.today()
        external_name = soup.find_all('span', itemprop="name")[-1].text
        external_category = soup.find_all('span', itemprop="name")[1].text.strip().rstrip()
        external_link = response.url
        description = ''
        try:
            for item in soup.find('table', id="product-attribute-specs-table").find('tbody').find_all('tr'):
                # description += item.xpath('.//th/text()').get() + ': ' + item.xpath('.//td/text()').get() + ' - '
                description += item.find('th').text + ': ' + item.find('td').text + ' - '
        except:
            pass
        pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
        possibilities = pattern.findall(str(response.text))
        for item in possibilities:
            if '"type":"image"' in item:
                jsonText = item
                break
        images = []
        if jsonText:
            jsonData = json.loads(jsonText.replace('\\n', ''))
            for image in jsonData['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']:
                image_src = image['full']
                images.append(unquote(image_src).replace('\\/', '/'))
        # price = response.xpath('//meta[@property="product:price:amount"]/@content').get()
        try:
            price = soup.find('meta', property="product:price:amount")['content']
        except:
            price = ''
        
        models_data = [{
                'external_id': external_id,
                'name': external_name,
                'description': '',
                'price': price
                }]

        self.threadResults.append({
            'external_category': external_category,
            'external_link': external_link,
            'external_name': external_name,
            'description': description,
            'brand': external_name.split(' ')[0],
            'external_id': external_id,
            'scraping_date': scraping_date,
            'models': models_data,
            'images': images
        })