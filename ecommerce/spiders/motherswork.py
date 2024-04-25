import json
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

categories = list()
domain = 'https://motherswork.com.sg'

x = requests.request("GET", domain, headers=headers)
if x.status_code == 200:
    content = x.text
    content_soup = BS(content, "html.parser")

    lvl1 = content_soup.find("div", {"id": "navigation"}).find("ul")
    lvl1_cats = lvl1.find_all("li", recursive=False)
    for lvl1_cat in lvl1_cats:
        if lvl1_cat.find("ul", {"class": "submenu"}) and \
                lvl1_cat.find("ul", {"class": "submenu"}).text.strip() != '':
            lvl2 = lvl1_cat.find("ul", {"class": "submenu"})
            lvl2_cats = lvl2.find_all("li", recursive=False)
            for lvl2_cat in lvl2_cats:
                if lvl2_cat.find("ul", {"class": "nested"}) and \
                        lvl2_cat.find("ul", {"class": "nested"}).text.strip() != '':
                    lvl3 = lvl2_cat.find("ul", {"class": "nested"})
                    lvl3_cats = lvl3.find_all("li", recursive=False)
                    for lvl3_cat in lvl3_cats:
                        cat_link = lvl3_cat.find('a', href=True)['href']
                        cat_link = domain + cat_link if domain not in cat_link else cat_link
                        categories.append(cat_link)
                else:
                    cat_link = lvl2_cat.find('a', href=True)['href']
                    cat_link = domain + cat_link if domain not in cat_link else cat_link
                    categories.append(cat_link)


class Spider(BaseSpider):
    name = 'motherswork'
    site_id = 27
    start_urls = categories
    site_name = 'Motherswork'
    site_url = 'https://motherswork.com.sg'
    site_favicon = 'https://cdn.shopify.com/s/files/1/0004/0855/1482/t/24/assets/favicon.png'
    logo = 'https://cdn.shopify.com/s/files/1/0004/0855/1482/files/motherswork_logo-01_600x.png?v=1614581499'

    custom_settings = {
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 8,
    }

    def parse(self, response):

        link = response.request.url
        external_category = response.meta.get('external_category') if response.meta.get('external_category') else link.replace((domain + '/'), '').strip()
        products = response.xpath('//div[@id="product-loop"]/div').extract()

        for product in products:
            try:
                prod_soup = BS(product, "html.parser")
                external_link = domain + prod_soup.find('div', {"class": "product-info"}).find('a', href=True)['href']

                external_name = prod_soup.find('div', {"class": "product-info"}).find('h3').get_text()
                external_name = re.sub(r'[\r\n\t]+', ' ', external_name).strip().rstrip()

                image = prod_soup.find('div', {"class": "prod-image"}).find('img')['src']
                image = image[:image.rfind('?')]

                yield scrapy.Request(external_link, callback=self.parse_product, dont_filter=True,
                                     meta={'external_category': external_category,
                                           'external_link': external_link,
                                           'external_name': external_name,
                                           'image': image})

            except Exception as err:
                print(err)

        # follow next page links
        pagination = BS(response.xpath('//div[@id="pagination"]').get(), "html.parser")
        next_page = pagination.find_all('a')
        if len(next_page) > 0:
            for a in next_page:
                if a.find('i', {'class': "fa fa-angle-right"}):
                    next_href = a['href']
                    next_href = domain + next_href if domain not in next_href else next_href
                    yield scrapy.Request(url=next_href, meta={'external_category': external_category})

    def parse_product(self, response):
        try:
            external_category = response.meta.get('external_category')
            external_link = response.meta.get('external_link')
            external_name = response.meta.get('external_name')
            image = response.meta.get('image')

            script_divs = response.xpath("//script").extract()
            for div in script_divs:
                if "window.hulkapps.product" in div:
                    json_data = re.search('window\.hulkapps\.product\s=.+', div)[0].split('window.hulkapps.product = ')[1]
                    try:
                        json_data = json.loads(json_data)
                    except:
                        json_data = None
                    break

            if json_data:
                external_id = json_data['id'] if json_data['id'] else ''

                brand = json_data['vendor'] if json_data['vendor'] else ''

                external_name = json_data['title']

                description = BS(json_data['description'], "html.parser").text
                description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()

                if json_data['available']:
                    item_price = json_data['price']/100.0
                else:
                    item_price = 0

                images = json_data['images'] if json_data['images'] else ''

                models = list()
                for i in json_data['variants']:
                    model_id = i['id'] if i['id'] else external_id
                    name = i['title']
                    if i['available']:
                        price = i['price']/100.0
                    else:
                        price = 0
                    model_image = i['featured_image']['src'] if i['featured_image'] else image
                    if price != 0:
                        models.append({
                            "external_id": model_id,
                            "name": name,
                            "price": price,
                            "image": model_image
                        })
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

            else:
                return

        except Exception as e:
            print(e)
