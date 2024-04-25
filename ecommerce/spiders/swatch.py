import json
import re
from ecommerce.spiders.base_spider import BaseSpider
import requests
import scrapy
from bs4 import BeautifulSoup as BS

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0"}
domain = 'https://www.swatch.com/en-sg/'


class Spider(BaseSpider):
    name = 'swatch'
    site_id = 29
    site_name = 'Swatch'
    site_url = 'https://www.swatch.com/en-sg/'
    site_favicon = 'https://www.swatch.com/on/demandware.static/Sites-swarp-ASIA-Site/-/default/dwc44fd3a5/images/favicons/swatch/favicon-16x16.png'
    logo = 'https://www.swatch.com/on/demandware.static/-/Library-Sites-swarp-global/default/dw1ec0978f/images/logo/swatch-logo.svg'

    def start_requests(self):

        try:
            x = requests.request("GET", 'https://www.swatch.com/en-sg/sw/', headers=headers)
            if x.status_code == 200:
                content = x.text
                content_soup = BS(content, "html.parser")
                btn = content_soup.find("div", {"class": "b-load_more"}).find('a', href=True)['href'].strip()
                sub = re.search('start=.*', btn)[0]

                count = int(content_soup.find("span", {"class": "b-search_result_count-inner"}).text.replace('products', '').strip())

                n = 0
                while n+200 < count:
                    new_link = btn.replace(sub, 'start=%d&sz=%d' % (n, 200))
                    yield scrapy.Request(new_link, callback=self.parse, dont_filter=True)
                    n += 200

                if n < count:
                    new_link = btn.replace(sub, 'start=%d&sz=%d' % (n, count-n))
                    yield scrapy.Request(new_link, callback=self.parse, dont_filter=True)

        except Exception as e:
            print(e)

    def parse(self, response):

        products = response.xpath('//body/div').extract()
        for item in products:
            try:
                item_soup = BS(item, "html.parser").find('div').find('div')

                # skip load more div
                if not item_soup:
                    continue

                product = json.loads(item_soup['data-product'])
                external_link = domain + product['id'] + '.html'

                yield scrapy.Request(external_link, callback=self.parse_product, dont_filter=True,
                                     meta={'external_link': external_link,
                                           'product': product,
                                           })

            except Exception as err:
                print(err)
                continue

    def parse_product(self, response):
        try:
            external_link = response.meta.get('external_link')

            product = response.meta.get('product')
            external_category = 'Watches'
            brand = product['brand']

            external_id = product['id']

            category = BS(response.xpath('//div[@class="b-pdp_tile-header"]').get(), "html.parser").text
            category = re.sub(r'[\r\n\t\s]+', ' ', category.strip()).strip()

            external_name = ' '.join(['Swatch', category, external_id])

            item_price = product['price']['sales']['value']

            images = list()
            for img in product['images']['medium']:
                images.append(img['url'])

            description = response.xpath('//meta[@property="og:description"]/@content').get()

            models = [{"external_id": external_id,
                       "name": external_name,
                       "price": item_price,
                       "image": images[0]
                       }]

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
