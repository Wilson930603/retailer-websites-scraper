import json
import re
from ecommerce.spiders.base_spider import BaseSpider
import requests
import scrapy
from bs4 import BeautifulSoup as BS

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0"}
domain = 'https://www.toysrus.com.sg/'


class Spider(BaseSpider):
    name = 'toysrus'
    site_id = 30
    site_name = 'Toys R Us - Singapore'
    site_url = 'https://www.toysrus.com.sg/'
    site_favicon = 'https://www.toysrus.com.sg/on/demandware.static/Sites-ToysRUs_SG-Site/-/default/dwe69a327a/images/favicon/favicon-tru.ico'
    logo = 'https://www.toysrus.com.sg/on/demandware.static/Sites-ToysRUs_SG-Site/-/default/dw23674d44/images/logo/tru.svg'

    custom_settings = {
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
    }

    def start_requests(self):
        categories = list()

        try:
            x = requests.request("GET", 'https://www.toysrus.com.sg/toysrus/?viewAllCategories=true', headers=headers)
            if x.status_code == 200:
                content = x.text
                content_soup = BS(content, "html.parser")

                sections = content_soup.find_all("div", {"class": "search-category-item"})
                for section in sections:
                    cat_link = section.find('a', href=True)['href']
                    cat_link = domain + cat_link if domain not in cat_link else cat_link
                    cat_link = cat_link + '?viewAll=true'

                    if 'batteries' in cat_link:
                        categories.append(cat_link)
                        continue

                    x = requests.request("GET", cat_link, headers=headers)
                    if x and x.status_code == 200:
                        content = x.text
                        content_soup = BS(content, "html.parser")
                        txt = content_soup.find("div", {"class": "result-count text-center"}).text.strip()
                        count = txt[txt.find('/') + 1:].replace('products', '').strip()
                        btn = content_soup.find("div", {"class": "show-more"}).find('button')
                        sub = re.search('start=.*', btn['data-url'])[0]
                        new_link = btn['data-url'].replace(sub, 'start=0&sz=%s' % count)
                        categories.append(new_link)
        except:
            print('Toys R Us Spider: Failed to get Categories/ start urls')

        for cat_link in categories:
            yield scrapy.Request(cat_link, callback=self.parse, dont_filter=True)

    def parse(self, response):

        products = response.xpath('//div[@class="card product-tile product"]').extract()
        for product in products:
            try:

                product = BS(product, "html.parser").find('div')

                external_link = product.find('a', href=True)['href']
                external_link = domain + external_link if domain not in external_link else external_link

                data = json.loads(product['data-metadata'])

                external_id = data['id']

                external_name = data['name']

                brand = data['brand']

                external_category = data['category']

                try:
                    item_price = data['price']
                except:
                    item_price = 0

                yield scrapy.Request(external_link, callback=self.parse_product, dont_filter=True,
                                     meta={'external_link': external_link,
                                           'external_category': external_category,
                                           'external_id': external_id,
                                           'external_name': external_name,
                                           'brand': brand,
                                           'item_price': item_price,
                                           })

            except Exception as err:
                print(err)
                pass

    def parse_product(self, response):
        external_link = response.meta.get('external_link')

        external_category = response.meta.get('external_category')

        external_id = response.meta.get('external_id')

        external_name = response.meta.get('external_name')

        brand = response.meta.get('brand')

        item_price = response.meta.get('item_price')

        div = response.xpath('//script[@type="application/ld+json"]').get()
        if "@context" in div:
            try:
                soup = BS(div, "html.parser").find('script')
                data = json.loads(soup.contents[0].strip())

                description = BS(data['description'], "html.parser").text

                images = data['image']

                models = list()
                models.append({
                    "external_id": external_id,
                    "name": external_name,
                    "price": item_price,
                    "image": images[0]
                })
                yield {
                    'external_category': external_category,
                    'external_link': external_link,
                    'external_name': external_name,
                    'description': description,
                    'brand': brand,
                    'external_id': external_id,
                    'models': models,
                    'images': images
                }
            except Exception as err:
                print(err)
