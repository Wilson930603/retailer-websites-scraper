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

brands = list()
x = requests.request("GET", 'https://www.mothercare.com.sg/shop-brand', headers=headers)
if x.status_code == 200:
    content = x.text
    content_soup = BS(content, "html.parser")
    divs = content_soup.findAll("div", {"class": "facets-category-cell"})
    for i in divs:
        brands.append(i.text.strip())

categories = list()
domain = 'https://www.mothercare.com.sg'

x = requests.request("GET", domain, headers=headers)
if x.status_code == 200:
    content = x.text
    content_soup = BS(content, "html.parser")

    lvl1 = content_soup.find("ul", {"class": "header-menu-level1"})
    lvl1_cats = lvl1.find_all("li", recursive=False)
    for lvl1_cat in lvl1_cats:
        if lvl1_cat.find("ul", {"class": "header-menu-level2"}) and \
                lvl1_cat.find("ul", {"class": "header-menu-level2"}).text.strip() != '':
            lvl2 = lvl1_cat.find("ul", {"class": "header-menu-level2"})
            lvl2_cats = lvl2.find_all("li", recursive=False)
            for lvl2_cat in lvl2_cats:
                if lvl2_cat.find("ul", {"class": "header-menu-level3"}) and \
                        lvl2_cat.find("ul", {"class": "header-menu-level3"}).text.strip() != '':
                    lvl3 = lvl2_cat.find("ul", {"class": "header-menu-level3"})
                    lvl3_cats = lvl3.find_all("li", recursive=False)
                    for lvl3_cat in lvl3_cats:
                        categories.append(domain + lvl3_cat.find('a', href=True)['href'])
                else:
                    categories.append(domain + lvl2_cat.find('a', href=True)['href'])


class Spider(BaseSpider):
    name = 'mothercare'
    site_id = 26
    start_urls = categories
    site_name = 'MotherCare'
    site_url = 'https://www.mothercare.com.sg'
    site_favicon = 'https://www.mothercare.com.sg/app/mcfavicon/img/favicon.ico'
    logo = 'https://www.mothercare.com.sg/app/img/mc-logo.png'

    def parse(self, response):

        link = response.request.url
        products = response.xpath('//div[@class="facets-items-collection-view-cell-span3"]').extract()

        for product in products:
            try:
                prod_soup = BS(product, "html.parser")
                external_name = prod_soup.find('a', {"class": "facets-item-cell-grid-title"}, href=True).get_text()

                brand = ''
                for i in brands:
                    if external_name.lower().startswith(i.lower()):
                        brand = i.capitalize()
                        break

                external_name = re.sub(r'[\r\n\t]+', ' ', external_name).strip().rstrip()
                external_link = domain + prod_soup.find('a', {"class": "facets-item-cell-grid-title"}, href=True)['href']
                image = prod_soup.find('img')['src']
                image = image[:image.rfind('?')]
                yield scrapy.Request(external_link, callback=self.parse_product, dont_filter=True,
                                     meta={'external_link': external_link,
                                           'external_name': external_name,
                                           'image': image,
                                           'brand': brand})

            except Exception as err:
                print(err)
                pass

        # follow next page links
        next_page = response.xpath('.//a[@class="global-views-pagination-next-link"]/@href').extract()
        if next_page and domain + next_page[0] != link:
            next_href = next_page[0]
            next_page_url = domain + next_href
            yield scrapy.Request(url=next_page_url)

    def parse_product(self, response):
        external_link = response.meta.get('external_link')
        external_name = response.meta.get('external_name')
        image = response.meta.get('image')
        brand = response.meta.get('brand')

        external_category = BS(response.xpath('//ul[@class="global-views-breadcrumb"]').get(), "html.parser").text if response.xpath('//ul[@class="global-views-breadcrumb"]').get() else ''

        images = response.xpath("//div[@class='product-details-image-gallery']//img/@src").getall()
        images = [image[:image.rfind('?')] for image in images]

        external_id = response.xpath("//span[@class='product-line-sku-value']/text()").get() if response.xpath("//span[@class='product-line-sku-value']/text()") else ''
        external_id = external_id.strip()

        # item_price = response.xpath('//meta[@itemprop="price"]/@content').get() if response.xpath('//meta[@itemprop="price"]/@content').get() else response.xpath('//meta[@itemprop="lowPrice"]/@content').get()
        if response.xpath('//span[@class="product-views-price-lead product-price-text_red"]'):
            item_price = BS(response.xpath('//span[@class="product-views-price-lead product-price-text_red"]').get(), "html.parser").text
        elif response.xpath('//span[@class="product-views-price-lead"]'):
            item_price = BS(response.xpath('//span[@class="product-views-price-lead"]').get(), "html.parser").text
        else:
            item_price = ''
        item_price = item_price.replace('S', '').replace('$', '').strip()

        if not item_price or item_price == '':
            print('Error Price: ' + external_link)

        # description = BS(response.xpath('//div[@class="item-details-description-area proper-text"]').get(), "html.parser").text if response.xpath('//div[@class="item-details-description-area proper-text"]').get() else ''
        if response.xpath('//meta[@property="og:description"]/@content'):
            description = response.xpath('//meta[@property="og:description"]/@content').get()
        else:
            description = ''
        description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()

        models = list()
        option_div = response.xpath("//div[@class='product-details-options-selector-option-container']")
        options = option_div.xpath("./div[starts-with(@class, 'product-views-option-')]").getall()
        try:
            if options and len(options) > 0:
                for option in options:
                    option = BS(option, "html.parser")
                    param = option.find('div')['class'][0]
                    param = param.replace('product-views-option-', '').strip()
                    if param == 'tile':
                        param = 'size'
                    choices = option.find('div').find_all('input')
                    for choice in choices:
                        name = choice.find_parent().text
                        if name == '':
                            name = choice['data-label-value']
                        value = choice['value']
                        x = requests.request("GET", external_link + '?%s=%s' % (param, value), headers=headers)
                        if x and x.status_code == 200:
                            # price = response.xpath('//meta[@itemprop="price"]/@content').get() if response.xpath(
                            #     '//meta[@itemprop="price"]/@content').get() else response.xpath(
                            #     '//meta[@itemprop="lowPrice"]/@content').get()
                            # price = price.strip()
                            if response.xpath('//span[@class="product-views-price-lead product-price-text_red"]'):
                                price = BS(response.xpath(
                                    '//span[@class="product-views-price-lead product-price-text_red"]').get(),
                                                "html.parser").text
                            elif response.xpath('//span[@class="product-views-price-lead"]'):
                                price = BS(response.xpath('//span[@class="product-views-price-lead"]').get(),
                                                "html.parser").text
                            else:
                                price = ''
                            price = price.replace('S', '').replace('$', '').strip()

                            if not price or price == '':
                                pass
                                # print('Error Model Price: ' + external_link)
                            else:
                                models.append({
                                    "external_id": external_id,
                                    "name": name,
                                    "price": price,
                                    "image": image
                                })

        except Exception as e:
            print(e)
            pass
        if len(models) == 0:
            models.append({
                "external_id": external_id,
                "name": external_name,
                "price": item_price,
                "image": image
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
