import json
import re
from ecommerce.spiders.base_spider import BaseSpider
import requests
import scrapy
from bs4 import BeautifulSoup as BS

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0"}
domain = 'https://www.chrono24.sg'


class Spider(BaseSpider):
    name = 'chrono24'
    site_id = 24
    site_name = 'Chrono24'
    site_url = 'https://www.chrono24.sg'
    site_favicon = 'https://static.chrono24.com/images/default/favicon/favicon.ico'
    logo = 'https://www.chrono24.sg/images/default/favicon/android-chrome-192x192.png'

    def start_requests(self):
        brands = list()

        try:
            x = requests.request("GET", 'https://www.chrono24.sg/search/browse.htm?char=A-Z', headers=headers)
            if x.status_code == 200:
                content = x.text
                content_soup = BS(content, "html.parser")

                div = content_soup.find("div", {"class": "brand-list"})
                sections = div.find_all("li")
                for section in sections:
                    brand_link = section.find('a', href=True)['href']
                    brand_link = domain + brand_link if domain not in brand_link else brand_link
                    brands.append(brand_link)
        except:
            print('Chrono24 Spider: Failed to get Brands/ start urls')

        for brand_link in brands:
            yield scrapy.Request(brand_link, callback=self.parse, dont_filter=True)

    def parse(self, response):

        products = response.xpath('//div[@id="wt-watches"]//div[@class="article-item-container wt-search-result"]').extract()
        for product in products:
            try:

                product = BS(product, "html.parser").find('div')

                external_link = product.find('a', href=True)['href']
                external_link = domain + external_link if domain not in external_link else external_link

                yield scrapy.Request(external_link, callback=self.parse_product, dont_filter=True,
                                     meta={'external_link': external_link,
                                           })

            except Exception as err:
                print(err)
                continue

        # follow next page links
        next_page = response.xpath('//div[@class="result-page-list-paging"]//a[@class="paging-next"]/@href').extract()
        if next_page and next_page[0]:
            next_page_url = domain + next_page[0] if domain not in next_page[0] else next_page[0]
            yield scrapy.Request(url=next_page_url)

    def parse_product(self, response):
        external_link = response.meta.get('external_link')

        external_category = 'Watches'

        description = response.xpath('//meta[@name="description"]/@content').get()

        try:
            tables = response.xpath('//table').getall()
            for data in tables:
                if 'Basic Info' in data:
                    table = BS(data, "html.parser")
                    cells = table.findAll('td')
                    for cell in cells:
                        if cell.find('h3'):
                            description += '; ' + re.sub(r'[\r\n\t\s]+', ' ', cell.text.strip()).strip()
                        elif cell.find('strong'):
                            description += ', ' + re.sub(r'[\r\n\t\s]+', ' ', cell.text.strip()).strip()
                        else:
                            description += ': ' + re.sub(r'[\r\n\t\s]+', ' ', cell.text.strip()).strip()
                    break

        except Exception:
            print('Description not complete: ' + external_link)

        try:
            script_divs = response.xpath("//script").getall()
            for div in script_divs:
                if "@context" in div:
                    soup = BS(div, "html.parser").find('script')
                    data = json.loads(soup.contents[0].strip())

                    for i in data['@graph']:
                        if i['@type'] == 'Product':
                            item = i

                            external_id = i['productID']

                            external_name = i['name']

                            brand = i['brand']

                            item_price = item['offers']['price']

                            images = list()
                            for img in item['image']:
                                images.append(img['contentUrl'])

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
                    break

        except Exception as err:
            print(err)
            return
