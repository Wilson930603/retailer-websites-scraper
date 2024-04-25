from ecommerce.spiders.base_spider import BaseSpider
from datetime import datetime
import requests
import json
from bs4 import BeautifulSoup
import string
from threading import Thread
from scrapy.utils.project import get_project_settings
import random
import re

settings = get_project_settings()
proxies = open(settings.get('ROTATING_PROXY_LIST_PATH')).read().split('\n')

headers = {
    'authority': 'www.carousell.sg',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'accept-language': 'en-US,en;q=0.9,ko;q=0.8',
}
categories = [
  ('https://www.carousell.sg/categories/computers-tech-213/', 'Computers & Tech'),
  ('https://www.carousell.sg/categories/mobile-phones-gadgets-215/', 'Mobile Phones & Gadgets'),
  ('https://www.carousell.sg/categories/luxury-20/', 'Luxury'),
  ('https://www.carousell.sg/categories/video-gaming-264/', 'Video Gaming'),
  ('https://www.carousell.sg/categories/audio-207/', 'Audio'),
  ('https://www.carousell.sg/categories/photography-6/', 'Photography'),
  ('https://www.carousell.sg/categories/tv-home-appliances-30/', 'TV & Home Appliances'),
  ('https://www.carousell.sg/categories/babies-kids-19/', 'Babies & Kids'),
  ('https://www.carousell.sg/categories/hobbies-toys-5934/', 'Hobbies & Toys'),
  ('https://www.carousell.sg/categories/health-nutrition-5953/', 'Health & Nutrition')
]

searchContext = ''
searchSession = ''
searchId = ''

class Spider(BaseSpider):
    name = 'carousell'
    stop = False
    start_urls = ['https://www.carousell.sg/']

    site_id = 6
    site_name = 'Carousell'
    site_url = 'https://www.carousell.sg'
    site_favicon = 'https://mweb-cdn.karousell.com/static/favicon.ico'
    logo = 'https://mweb-cdn.karousell.com/build/carousell-logo-title-2Nnf7YFiNk.svg'

    threadResults = []
    threads = []
    scraped = []
    concurrent = settings.get('CONCURRENT_REQUESTS')
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
    }

    def parse(self, response):
        global searchContext, searchSession, searchId
        for category in categories:
            self.scraped = []
            self.stop = False
            r = requests.get(category[0], headers=headers)
            r = r.text.split("window.initialState=")[1].split("</script>")[0].strip(" ;")
            json_data = json.loads(r)
            searchContext = json_data["SearchListing"]["parameters"]["searchContext"]
            searchSession = json_data["SearchListing"]["parameters"]["session"]
            searchId = json_data["SearchListing"]["parameters"]['searchId']

            while not self.stop:
                data = {
                    "bestMatchEnabled": True,"canChangeKeyword": False,"ccid": 361,"count": 20,"countryCode": "SG","countryId": "1880251",
                    "filters": [{"fieldName": "collections","idsOrKeywords": {"value": ["213"]},"enforce": True}],
                    "includeSuggestions": False,"locale": "en","prefill": {},"query": None,
                    "searchContext": searchContext,"session": searchSession
                }
                while True:
                    proxy = random.choice(proxies)
                    try:
                        response = requests.post('https://www.carousell.sg/api-service/search/cf/4.0/search/', headers=headers, json=data, proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'})
                        jsonResponse = response.json()
                        break
                    except Exception as err:
                        print(err)
                        pass
                try:
                    if len(jsonResponse['data']['results']) == 0:
                        self.stop = True
                        continue
                except:
                    self.stop = True
                    continue
                searchContext = jsonResponse['data']['searchContext']
                searchSession = jsonResponse['data']['session']
                for item in jsonResponse['data']['results']:
                    card = item['listingCard'] if 'listingCard' in item else item['promotedListingCard']['listingCard']
                    if any(x.lower() in card['belowFold'][3]['stringContent'].lower() for x in ['brand new', 'like new']):
                        product_id = card['id']
                        external_name = card['title'].replace(' ', '-')
                        for c in string.punctuation:
                            external_name = external_name.replace(c," ")
                        external_name = external_name.replace(' ', '-')
                        while '--' in external_name:
                            external_name = external_name.replace('--', '-')
                        external_name = external_name.strip()
                        product_price = card['price'].replace('S$', '').replace(',', '')
                        external_link = 'https://www.carousell.sg/p/' + external_name + '-' + product_id + '/?searchId=' + searchId
                        t = Thread(target=self.scrapeProduct, args=(external_link, product_id, external_name, product_price, category[1]))
                        t.start()
                        self.threads.append(t)
                for thread in self.threads:
                    thread.join()
                for data in self.threadResults:
                    print(data)
                    yield data
                self.threads = []
                self.threadResults = []
            self.stop = False
            continue

    def scrapeProduct(self, external_link, product_id, external_name, product_price, catgoryName):
        while True:
            proxy = random.choice(proxies)
            try:
                r = requests.get(external_link, headers=headers, proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'}, timeout=10)
                break
            except:
                pass 
        soup = BeautifulSoup(r.text, 'lxml')
        external_category = catgoryName
        external_id = product_id
        possibleBrands = []
        for section in soup.find_all('section'):
            for p in section.find_all('p'):
                possibleBrands.append(p)

        brand = ''
        for item in possibleBrands:
            if 'Brand' in item:
                brand = possibleBrands[possibleBrands.index(item)+1].text
                break
        try:
            dataJson = json.loads(soup.find('script', type='application/ld+json').contents[0])
            description = re.sub(r'[^\x00-\x7F]',' ', dataJson['description']).replace('\n', ' ').replace('\r', ' ') if 'description' in dataJson else ''
            images = dataJson['image']
        except:
            description = images = ''
        scraping_date = datetime.today()
        models_data = [{
                'external_id': external_id,
                'name': "".join(c for c in external_name if ord(c) < 128),
                'description': "".join(c for c in description if ord(c) < 128),
                'price': product_price
                }]

        self.threadResults.append({
            'external_category': external_category,
            'external_link': external_link,
            'external_name': external_name,
            'description': description,
            'brand': brand,
            'external_id': external_id,
            'scraping_date': scraping_date,
            'models': models_data,
            'images': images
        })