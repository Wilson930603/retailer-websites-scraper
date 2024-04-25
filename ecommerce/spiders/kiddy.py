import json
import re
from ecommerce.spiders.base_spider import BaseSpider
import requests
import scrapy
from bs4 import BeautifulSoup as BS

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0"}
domain = 'https://kiddypalace.com.sg'


class Spider(BaseSpider):
    name = 'kiddy'
    site_id = 25
    site_name = 'Kiddy Palace Pte Ltd'
    site_url = 'https://kiddypalace.com.sg'
    site_favicon = 'https://cdn.shopify.com/s/files/1/0592/3127/3146/files/favicon-01_f42a0ecc-a848-472e-b2b2-05eee3f48aa4_32x32.jpg'
    logo = 'https://cdn.shopify.com/s/files/1/0592/3127/3146/files/KP_logo-01_360x.jpg?v=1628730996'

    def start_requests(self):
        categories = list()

        try:
            x = requests.request("GET", domain, headers=headers)
            if x.status_code == 200:
                content = x.text
                content_soup = BS(content, "html.parser")

                sections = content_soup.find_all("div", {"class": "collection-grid-item"})
                for section in sections:
                    cat_link = section.find('a', href=True)['href']
                    cat_link = domain + cat_link if domain not in cat_link else cat_link
                    categories.append(cat_link)
        except:
            print('kiddy Spider: Failed to get Categories/ start urls')

        for cat_link in categories:
            yield scrapy.Request(cat_link, callback=self.parse, dont_filter=True)

    def parse(self, response):

        link = response.request.url
        external_category = response.meta.get('external_category') if response.meta.get('external_category') else link.replace((domain + '/collections/'), '').strip()

        products = response.xpath('//div[starts-with(@class, "product__title")]//a/@href').extract()
        for external_link in products:
            try:
                external_link = domain + external_link if domain not in external_link else external_link
                yield scrapy.Request(external_link, callback=self.parse_product, dont_filter=True,
                                     meta={'external_link': external_link,
                                           'external_category': external_category,
                                           })

            except Exception as err:
                print(err)
                pass

        # follow next page links
        next_page = response.xpath('//div[starts-with(@class, "pagination")]//span[@class="next"]//a/@href').extract()
        if next_page and next_page[0]:
            next_page_url = domain + next_page[0] if domain not in next_page[0] else next_page[0]
            yield scrapy.Request(url=next_page_url, meta={'external_category': external_category})

    def parse_product(self, response):
        external_link = response.meta.get('external_link')

        external_category = response.meta.get('external_category')

        description = response.xpath('//meta[@property="og:description"]/@content').get() if response.xpath('//meta[@property="og:description"]/@content') else ''
        description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()

        script_divs = response.xpath("//script").getall()

        for div in script_divs:
            soup = BS(div, "html.parser").find('script')
            if soup.has_attr("id") and soup["id"] == 'ProductJson-product-template':
                try:

                    data = json.loads(soup.contents[0].strip())
                    external_id = data['id']

                    external_name = data['title']

                    brand = data['vendor']

                    try:
                        item_price = data['price'] / 100.0
                    except:
                        item_price = 0

                    images = data['images']

                    models = list()
                    variants = data['variants']
                    # No models / choices in this product
                    if len(variants) == 0:
                        models.append({"external_id": external_id,
                                       "name": external_name,
                                       "price": item_price,
                                       "image": images[0]
                                       })
                    else:
                        for option in variants:
                            option_id = option['id']
                            name = option['name']
                            price = option['price'] / 100.0
                            try:
                                model_image = option['featured_image']['src'] if option['featured_image'] else ''
                            except:
                                model_image = ''
                            if price != 0:
                                models.append({
                                    "external_id": option_id,
                                   "name": name,
                                   "price": price,
                                   "image": model_image
                            })

                except Exception as err:
                    print(err)
                    return
                break
        if models:
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
