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

categories = list()
sitemap = 'https://www.harveynorman.com.sg/sitemap'

x = requests.request("GET", sitemap, headers=headers)
if x.status_code == 200:
    content = x.text
    content_soup = BS(content, "html.parser")

    sitemap = content_soup.find("div", {"class": "sitemap"})
    divs = sitemap.find_all("div")
    # print(len(divs))
    for div in divs:
        if 'Catalog' in div.find("h3").text:
            external_cats = div.find_all("li")
            # print(len(external_cats))
            for cat in external_cats:
                link = cat.find('a', href=True)['href']
                if link and link.startswith('//'):
                    categories.append('https:' + link)


class Spider(BaseSpider):
    name = 'harvey'
    start_urls = ['https://www.harveynorman.com.sg/']

    site_id = 14
    site_name = 'Harvey Norman'
    site_url = 'https://www.harveynorman.com.sg'
    site_favicon = 'https://hnsgsfp.imgix.net/4/images/logos/1/favicon_0z5s-yb.ico?fit=fill&bg=0FFF&w=16&h=16&auto=format,compress'
    logo = 'https://hnsgsfp.imgix.net/4/images/logos/1/hnsg-flag-logo-@x2.png?fit=fill&bg=0FFF&w=728&h=105&auto=format,compress'

    def parse(self, response):

        for category in categories:
            n = 1
            while True:
                website = category + 'page-%s' % str(n)
                # print(website)

                try:
                    r = requests.request("GET", website, headers=headers)
                    if r.status_code != 200:
                        break
                    content = r.text
                    content_soup = BS(content, "html.parser")
                    products = content_soup.find_all("div", {"class": "product-image"})

                    for product in products:
                        try:
                            link = 'https:' + product.find('a', href=True)['href']
                            # print(link)
                            yield scrapy.Request(link, headers=headers, callback=self.parse_product, dont_filter=True)

                        except Exception as err:
                            print(err)
                        # break for testing, only 1 item of category scraped
                        # break
                except:
                    continue
                n += 1

                # break for testing, only 1 page scraped
                # break

            # break for testing, only 1 category scraped
            # break

    def parse_product(self, response):
        external_category = ''
        try:
            external_category = BS(response.xpath('//div[@class="breadcrumbs-container"]//li').extract()[2], "html.parser").text
        except IndexError:
            external_category = BS(response.xpath('//div[@class="breadcrumbs-container"]//li').extract()[1], "html.parser").text
        external_link = response.request.url
        name = response.css('h1.product-title::text').get()
        price = BS(response.css('span.price').get(), "html.parser").text
        price = price.replace('S', '').replace('$', '').strip()
        try:
            price = float(price)
        except ValueError:
            pass
        images = response.xpath("//div[starts-with(@class, 'product-img-list')]//img/@src").getall()
        description = BS(response.xpath("//*[contains(@id, 'content_description')]").get(), "html.parser").text
        description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()
        description = description.replace('<br>', '').strip()
        scraping_date = datetime.today()

        external_id = response.css('small.product-id.meta::text').get()
        # try:
        #     external_id = int(external_id)
        # except ValueError:
        #     pass

        brand = ''
        try:
            spec_tabs = BS(response.xpath("//div[@id='content_features']").get(), "html.parser")
            # table = [tr.findAll('td') for tr in spec_tabs.findAll('tr')]
            for tr in spec_tabs.findAll('tr'):
                if 'Brand' in tr.getText():
                    brand = tr.find('td').getText()
                    break
        except Exception as e:
            # print(e)
            pass

        models = list()

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
            'scraping_date': scraping_date,
            'models': models,
            'images': images
        }
