import re
from ecommerce.spiders.base_spider import BaseSpider
from datetime import datetime
import requests
import scrapy

from bs4 import BeautifulSoup as BS

headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
            "X-Requested-With": "XMLHttpRequest",
            "If-None-Match-": "55b03-c627987a2d33ab84dec29c1611a0bcf5",
                }

categories = dict()
domain = 'https://megadiscountstore.com.sg'

x = requests.request("GET", domain, headers=headers)
if x.status_code == 200:
    content = x.text
    content_soup = BS(content, "html.parser")

    nav = content_soup.find("ul", {"class": "nav"})
    divs = nav.find_all("ul", {"class": "nav-subMenu"})
    for div in divs:
        external_cats = div.find_all("li")
        for cat in external_cats:
            link = domain + cat.find('a', href=True)['href']
            cat_label = cat.find('a', href=True).text
            if link:
                categories[cat_label] = link

# print(len(categories))

class Spider(BaseSpider):
    name = 'megastore'
    start_urls = ['https://megadiscountstore.com.sg/']

    site_id = 15
    site_name = 'Mega Discount Store'
    site_url = 'https://megadiscountstore.com.sg'
    site_favicon = 'https://cdn.shopify.com/s/files/1/0494/0761/t/2/assets/favicon.png?v=12060075014019195273'
    logo = 'https://cdn.shopify.com/s/files/1/0494/0761/t/2/assets/logo.png?v=662432556347979183'

    def parse(self, response):

        for external_category in categories:
            # print(external_category)

            link = categories[external_category]

            n = 1
            while True:
                website = link + '?page=%s' % str(n)
                # print(website)

                try:
                    r = requests.request("GET", website, headers=headers)
                    if r.status_code != 200:
                        break
                    content = r.text
                    content_soup = BS(content, "html.parser")
                    products = content_soup.find_all("li", {"class": "collectionItem"})

                    for product in products:
                        try:
                            brand = product.find("span", {"class": "prod-brand"}).get_text() if product.find("span", {"class": "prod-brand"}) else ''
                            external_link = domain + product.find("div", {"class": "prod-title"}).find('a', href=True)['href'] if product.find("div", {"class": "prod-title"}).find('a', href=True) else ''
                            name = product.find("div", {"class": "prod-title"}).find('a', href=True).get_text() if product.find("div", {"class": "prod-title"}).find('a', href=True) else ''
                            name = re.sub(r'[\r\n\t]+', ' ', name).strip().rstrip()
                            name = name.replace('<br>', ' ')
                            # name = name.lstrip(brand).strip()
                            # price = product.find("div", {"class": "prod-big-price"}).get_text() if product.find("div", {"class": "prod-big-price"}) else ''
                            # price = price.replace('S', '').replace('NOW', '').replace('$', '').replace(',', '').strip()
                            yield scrapy.Request(external_link, headers=headers, callback=self.parse_product, dont_filter=True,
                                                 meta={'external_category': external_category,
                                                       'external_link': external_link,
                                                       'external_name': name,
                                                       'brand': brand})
                                                       # 'price': price})
                        except Exception as err:
                            print(err)
                        # break for testing, only 1 product of category scraped
                        # break
                except:
                    continue

                if len(products) == 48:

                    # # limit 3 pages for good sample
                    # if n == 3:
                    #     break

                    n += 1
                    continue
                else:
                    break

            # break for testing, only 1 category scraped
            # break

    def parse_product(self, response):

        external_category = response.meta.get('external_category')
        external_link = response.meta.get('external_link')
        external_name = response.meta.get('external_name')
        brand = response.meta.get('brand')
        # price = response.meta.get('price')
        price = response.xpath('//meta[@property="og:price:amount"]/@content').get()
        price = price.replace('$', '').replace(',', '').strip()
        try:
            price = float(price)
        except ValueError:
            pass

        images = response.xpath("//div[starts-with(@id, 'product_slider')]//a/@href").getall()
        description = BS(response.xpath("//div[contains(@id, 'product-summary')]").get(),  "html.parser").text if response.xpath("//div[contains(@id, 'product-summary')]").get() else ''
        if description == '':
            description = BS(response.xpath("//*[contains(@id, 'shopify-product-information')]").get(), "html.parser").text
        description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()
        scraping_date = datetime.today()
        external_id = response.xpath("//*[contains(@id, 'looxReviews')]/@data-product-id").get()

        models = list()
        # try:
        #     option_soup = BS(response.xpath("//div[starts-with(@id, 'option_')]").get(), "html.parser")
        #     options = option_soup.find_all('option')
        #     if options and len(options) > 0:
        #         for option in options:
        #             models.append({"external_id": external_id,
        #                            "name": option.text.strip(),
        #                            "description": "",
        #                            "price": price})
        # except:
        models.append({"external_id": external_id,
                       "name": external_name,
                       "description": "",
                       "price": price})

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
