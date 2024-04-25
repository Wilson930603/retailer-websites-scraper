import json
import re
import time

from ecommerce.spiders.base_spider import BaseSpider
from datetime import datetime
import requests
import scrapy
from urllib.parse import urlencode

from bs4 import BeautifulSoup as BS

headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
            "X-Requested-With": "XMLHttpRequest",
            "If-None-Match-": "55b03-c627987a2d33ab84dec29c1611a0bcf5",
                }

categories = dict()
domain = 'https://audiohouse.com.sg/'

x = requests.request("GET", domain, headers=headers)
if x.status_code == 200:
    # print(x.request.url)
    content = x.text
    content_soup = BS(content, "html.parser")

    # nav = content_soup.find_all("div", {"class": "eight wide column"})
    divs = content_soup.find_all("div", {"class": "eight wide column"})
    for div in divs:
        label = div.find("h4", {"class": "ui header"})
        if 'All Products' in label:
            external_cats = div.find_all("a")
            for cat in external_cats:
                link = domain + cat['href']
                cat_label = cat.text
                if link:
                    categories[cat_label] = link


class Spider(BaseSpider):
    name = 'audiohouse'
    start_urls = ['https://audiohouse.com.sg/']

    site_id = 12
    site_name = 'Audio House'
    site_url = 'https://audiohouse.com.sg'
    site_favicon = 'https://audiohouse.com.sg/favicon.ico'
    logo = ''

    def parse(self, response):

        for external_category in categories:

            try:
                # print(external_category)

                n = 1
                finish = 'N'
                items = list()
                abb = categories[external_category][categories[external_category].find('category='):].replace('category=', '')

                while finish == 'N':
                    link = 'https://audiohouse.com.sg/search.php?category=%s&sort=0&page=%d' % (abb, n)
                    x = requests.request("GET", link, headers=headers)
                    if x.status_code == 200:
                        response = json.loads(x.text)
                        # print(response['total'])
                        finish = response['finish']
                        items += list(response['stks'])
                    n += 1

                # print(len(items))

                for item in items:
                    try:
                        item_dict = dict(item)
                        brand = item_dict['brand_name']
                        external_id = item_dict['stk_id']
                        external_link = 'https://audiohouse.com.sg/product.php?item=' + external_id
                        name = item_dict['name']
                        name = re.sub(r'[\r\n\t]+', ' ', name).strip().rstrip()
                        name = name.replace('<br>', ' ').strip()
                        # name = name.lstrip(brand).strip()
                        price = item_dict['net_price']
                        price = price.replace('$', '').replace(',', '').strip()
                        img = domain + item_dict['url_addr'] + '.jpg'
                        try:
                            price = float(price)
                        except ValueError:
                            pass
                        yield scrapy.Request(external_link, headers=headers, callback=self.parse_product, dont_filter=True,
                                             meta={'external_id': external_id,
                                                   'external_category': external_category,
                                                   'external_link': external_link,
                                                   'external_name': name,
                                                   'brand': brand,
                                                   'img': img,
                                                   'price': price})
                    except Exception as err:
                        print(err)
            except:
                continue

    def parse_product(self, response):
        external_id = response.meta.get('external_id')
        external_category = response.meta.get('external_category')
        external_link = response.meta.get('external_link')
        external_name = response.meta.get('external_name')
        brand = response.meta.get('brand')
        price = response.meta.get('price')
        img = response.meta.get('img')

        images = [img]
        description = BS(response.xpath("//div[contains(@class, 'ui bottom attached tab segment active')]").get(),  "html.parser").text if response.xpath("//div[contains(@class, 'ui bottom attached tab segment active')]").get() else ''
        description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()
        scraping_date = datetime.today()
        models = [
            {
                "external_id": external_id,
                "name": external_name,
                "description": "",
                "price": price
            }
        ]

        yield {
            'external_category': external_category,
            'external_link': external_link,
            'external_name': external_name,
            'description': description,
            'brand': brand,
            'external_id': external_id,
            'scraping_date': scraping_date,
            'models': models,
            'images': images
        }
