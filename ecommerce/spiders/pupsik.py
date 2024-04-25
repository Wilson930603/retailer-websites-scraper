import json
import re
from ecommerce.spiders.base_spider import BaseSpider
import requests
import scrapy
from bs4 import BeautifulSoup as BS

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0"}
domain = 'https://www.pupsikstudio.com'


class Spider(BaseSpider):
    name = 'pupsik'
    site_id = 28
    site_name = 'Pupsik Studio'
    site_url = 'https://www.pupsikstudio.com'
    site_favicon = 'https://www.pupsikstudio.com/media/favicon/websites/1/favicon.jpg'
    logo = 'https://cdn.knoji.com/images/logo/pupsikstudiocom.jpg?aspect=center&snap=false&width=500&height=250>'
    start_urls = ['https://www.pupsikstudio.com']

    custom_settings = {
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 4,
    }

    def parse(self, response):
        categories = list()
        try:
            content = response.text
            content_soup = BS(content, "html.parser")

            lvl1 = content_soup.find("nav", {"class": "navigation"}).find("ul")
            lvl1_cats = lvl1.select("li[class^=level0]", recursive=False)
            for lvl1_cat in lvl1_cats:
                if lvl1_cat.find("ul") and lvl1_cat.find("ul").text.strip() != '':
                    lvl2 = lvl1_cat.find("ul", recursive=False)
                    lvl2_cats = lvl2.select("li[class^=level1]", recursive=False)
                    for lvl2_cat in lvl2_cats:
                        cat_link = lvl2_cat.find('a', href=True)['href']
                        cat_link = domain + cat_link if domain not in cat_link else cat_link
                        if 'featured-products' in cat_link:
                            continue
                        elif 'whats-new' in cat_link:
                            continue
                        elif 'best-selling-products' in cat_link:
                            continue
                        else:
                            categories.append(cat_link)
        except:
            print('Pupsik Spider: Failed to get Categories/ start urls')

        for cat_link in categories:
            yield scrapy.Request(cat_link, callback=self.parse_cat, dont_filter=True)

    def parse_cat(self, response):

        link = response.request.url
        external_category = response.meta.get('external_category') if response.meta.get('external_category') else link.replace((domain + '/'), '').strip()

        products = response.xpath('//li[@class="item product product-item"]').extract()
        for product in products:
            try:
                prod_soup = BS(product, "html.parser")
                external_link = prod_soup.find('a', {"class": "product-item-link"}, href=True)['href']
                external_id = prod_soup.find('div', {"class": "price-box price-final_price"})['data-product-id']

                if external_link:
                    if domain not in external_link:
                        external_link = domain + external_link

                    yield scrapy.Request(external_link, callback=self.parse_product, dont_filter=True,
                                         meta={'external_category': external_category,
                                               'external_link': external_link,
                                               'external_id': external_id})

            except Exception as err:
                print(err)
                pass

        # follow next page links
        next_page = response.xpath('.//div[@class="pages"]//li[@class="item pages-item-next"]//a/@href').extract()
        if next_page and next_page[0]:
            next_page_url = domain + next_page[0] if domain not in next_page[0] else next_page[0]
            yield scrapy.Request(url=next_page_url, meta={'external_category': external_category})

    def parse_product(self, response):
        external_id = response.meta.get('external_id')

        external_category = response.meta.get('external_category')

        external_link = response.meta.get('external_link')

        external_name = response.xpath('//meta[@property="og:title"]/@content').get() if response.xpath('//meta[@property="og:title"]/@content') else ''
        external_name = re.sub(r'[\r\n\t]+', ' ', external_name).strip().rstrip()

        image = response.xpath('//meta[@property="og:image"]/@content').get() if response.xpath('//meta[@property="og:image"]/@content') else ''

        description = response.xpath('//meta[@property="og:description"]/@content').get() if response.xpath('//meta[@property="og:description"]/@content') else ''
        description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()

        brand = response.xpath("//div[@class='amshopby-option-list']//a/@title").get()

        item_price = response.xpath('//span[@id="product-price-%s"]/@data-price-amount'%external_id).get() if response.xpath('//span[@id="product-price-%s"]/@data-price-amount'%external_id) else 0

        images = list()
        script_divs = response.xpath("//script").extract()
        try:
            for div in script_divs:
                if "data" in div and "gallery-placeholder" in div and "magnifierOpts" in div:
                    json_data = re.search('"data"\s*:.+', div)[0].split('"data"')[1]
                    json_data = json_data.lstrip(':')
                    json_data = json_data.rstrip(',')
                    images_data = json.loads(json_data)
                    for i in images_data:
                        images.append(i['img'].replace(' ', ''))
                    break
        except Exception as e:
            print(e)
            images.append(image)

        models = list()
        try:
            for div in script_divs:
                if "spConfig" in div:
                    json_data = re.search('"spConfig"\s*:.+', div)[0].split('"spConfig"')[1]
                    json_data = json_data.strip()
                    json_data = json_data.lstrip(':').strip()
                    json_data = json_data.rstrip(',').strip()
                    options_data = json.loads(json_data)

                    for option in list(options_data['attributes'].values())[0]['options']:
                        option_id = option['id']
                        name = option['label']
                        price = options_data['optionPrices'][option['products'][0]]['finalPrice']['amount'] * 1.0
                        try:
                            model_image = '' if len(options_data['images']) == 0 else options_data['images'][option['products'][0]][0]['img']
                        except:
                            model_image = ''
                        if price != 0:
                            models.append({
                                "external_id": option_id,
                                "name": name,
                                "price": price,
                                "image": model_image
                            })
                    break
            else:
                raise Exception
        except Exception:
            # No models / choices in this product
            if not models and item_price != 0:
                models.append({
                    "external_id": external_id,
                    "name": external_name,
                    "price": item_price,
                    "image": image
                })
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
