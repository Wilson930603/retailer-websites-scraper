import re
from ecommerce.spiders.base_spider import BaseSpider
import requests
import scrapy

from bs4 import BeautifulSoup as BS

headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
            "X-Requested-With": "XMLHttpRequest",
            "If-None-Match-": "55b03-c627987a2d33ab84dec29c1611a0bcf5",
                }

domain = 'https://www.electronicscrazy.sg'


class Spider(BaseSpider):
    name = 'electronicscrazy'
    start_urls = ['https://www.electronicscrazy.sg/']

    site_id = 13
    site_name = 'Electronics Crazy'
    site_url = 'https://www.electronicscrazy.sg'
    site_favicon = 'https://www.electronicscrazy.sg/favicon.ico'
    logo = 'https://www.electronicscrazy.sg/images/logos/8/ec_logo_20.png'

    def start_requests(self):
        categories = dict()
        sitemap = 'https://www.electronicscrazy.sg/sitemap/'

        x = requests.request("GET", sitemap, headers=headers)
        if x.status_code == 200:
            content = x.text
            content_soup = BS(content, "html.parser")

            sitemap = content_soup.find("ul", {"class": "ty-sitemap__tree-list"})
            external_cats = sitemap.find_all("li")
            for cat in external_cats:
                link = cat.find('a', href=True)['href']
                link = domain + link if domain not in link else link
                cat_label = cat.find('a', href=True).text
                if link:
                    categories[cat_label] = link

        if len(categories) != 0:
            for external_category in categories:

                # Skip rent products
                if 'RENT' in external_category.upper():
                    continue

                cat_link = categories[external_category]
                yield scrapy.Request(cat_link, callback=self.parse, dont_filter=True, meta={'external_category': external_category})

    def parse(self, response):
        external_category = response.meta.get('external_category')
        link = response.request.url
        # print(link)
        content = response.text
        content_soup = BS(content, "html.parser")
        products = content_soup.find_all("div", {"class": "main-grid card-s"})

        for product in products:
            try:
                external_link = product.find('a', href=True)['href']
                external_link = domain + external_link if domain not in external_link else external_link

                yield scrapy.Request(url=external_link, headers=headers, callback=self.parse_product, dont_filter=True,
                                     meta={'external_category': external_category,
                                           'external_link': external_link})
            except Exception as err:
                print("parse: " + err)
                continue

        next_page = response.xpath(
            '//div[@class="pagination-container"]//ul[@class="pagination"]//li[@class="PagedList-skipToNext"]//a/@href').extract()
        if next_page and next_page[0]:
            next_page_url = domain + next_page[0] if domain not in next_page[0] else next_page[0]
            yield scrapy.Request(url=next_page_url, headers=headers, callback=self.parse, dont_filter=True,
                                 meta={'external_category': external_category})

    def parse_product(self, response):
        def create_param(listoflists, rslt=list(), rslt_data=list()):
            if len(listoflists) == 0:
                rslt_data.append(rslt)
            else:
                for i in listoflists[0]:
                    create_param(listoflists[1:], rslt + [i], rslt_data)
            return rslt_data

        external_category = response.meta.get('external_category')
        external_link = response.meta.get('external_link')

        external_id, name, price, is_variation, brand, description = '', '', '', '', '', ''
        inpts = response.xpath('//input').getall()
        for i in inpts:
            elem = BS(i, "html.parser").find('input')
            try:
                if elem['id'] and elem['id'] == 'CartProduct':
                    external_id = elem['item_sk']
                    name = elem['item_name'].strip()
                    price = elem['price']
                    try:
                        price = float(price)
                    except ValueError:
                        pass
                    is_variation = elem['is_variation']
                    break
            except:
                continue
        else:
            # Soldout product
            for i in inpts:
                try:
                    elem = BS(i, "html.parser").find('input')
                    if elem['id'] and elem['id'] == 'item_sk':
                        external_id = elem['value']
                    elif elem['id'] and elem['id'] == 'item_name':
                        name = elem['value'].strip()

                    if external_id != '' and name != '':
                        # price = 0
                        is_variation = "1"
                        break
                except:
                    continue

        try:
            images = response.xpath('//meta[@property="og:image"]/@content').getall()
            description = response.xpath('//meta[@property="og:description"]/@content').get()
            if description:
                description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()
                description = description.replace('<br>', '').strip()

            spec_tab = response.xpath("//div[starts-with(@class, 'grid-h1-product-details-brand')]").get()
            if spec_tab:
                spec_soup = BS(spec_tab, "html.parser")
                brand = spec_soup.find("div").getText()
                brand = brand.replace('Brand:', '').strip()
            else:
                spec_li = response.xpath("//li").extract()
                for li in spec_li:
                    spec_soup = BS(li, "html.parser").find("li")
                    brand = spec_soup.getText()
                    if 'Brand:' in brand:
                        brand = brand.replace('Brand:', '').strip()
                        break

        except Exception as e:
            print('parse_product:')
            print(e)
            pass

        models = list()
        if "0" in is_variation:
            models.append({"external_id": external_id,
                           "name": name,
                           "description": "",
                           "price": price})
        else:
            try:
                selects = response.xpath("//select[starts-with(@class, 'custom-select vairants_drop')]").getall()
                if len(selects) >= 1:
                    option_selects = list()
                    value_selects = list()

                    for i in range(len(selects)):
                        option_text = list()
                        option_value = list()

                        select_soup = BS(selects[i], "html.parser").find('select')
                        options = select_soup.findAll("option")
                        for j in range(len(options)):
                            option_value.append(options[j]['value'])
                            option_text.append(options[j]['variation_text'])

                        option_selects.append(option_value)
                        value_selects.append(option_text)

                    option_data = create_param(option_selects)
                    price_api = "https://www.electronicscrazy.sg/Home/getvariation_price"

                    for lst in option_data:
                        txt, price = '', ''
                        for i in range(len(lst)):
                            txt += value_selects[i][option_selects[i].index(lst[i])] + (
                                ', ' if i != (len(lst) - 1) else '')

                        data = {'item_sk': external_id, 'item_property': (','.join(lst)) + ','}
                        r = requests.post(price_api, data=data)
                        if r:
                            rjson = r.json()
                            if rjson and rjson['price']:
                                price = rjson['price']

                                models.append({"external_id": external_id,
                                               "name": txt,
                                               "description": "",
                                               "price": price})
            except Exception as e:
                print('parse_product2:')
                print(e)
                pass

        if len(models) == 0 and external_id != '' and name != '':
            models.append({"external_id": external_id,
                           "name": name,
                           "description": "",
                           "price": price})
        yield {
            'external_category': external_category,
            'external_link': external_link,
            'external_name': name,
            'description': description,
            'brand': brand,
            'external_id': external_id,
            'models': models,
            'images': images
        }
