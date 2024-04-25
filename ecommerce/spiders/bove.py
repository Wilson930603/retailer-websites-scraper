import json
import re
from ecommerce.spiders.base_spider import BaseSpider
import requests
import scrapy
from bs4 import BeautifulSoup as BS

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0"}
domain = 'https://bove.co'


class Spider(BaseSpider):
    name = 'bove'
    site_id = 23
    site_name = 'Bove'
    site_url = 'https://bove.co'
    site_favicon = 'https://cdn.shopify.com/s/files/1/2262/3821/files/Untitled_design_5_32x32.png'
    logo = 'https://cdn.shopify.com/s/files/1/2262/3821/files/Bove_By_Spring_Maternity-01_f4357f77-e030-401e-af41-632453a13ecb_890x300.png?v=1634302516'

    def start_requests(self):
        categories = list()

        try:
            x = requests.request("GET", domain, headers=headers)
            if x.status_code == 200:
                content = x.text
                content_soup = BS(content, "html.parser")

                lvl1 = content_soup.find("nav", {"class": "site-navigation"}).find("ul")
                lvl1_cats = lvl1.select("li[class^=navmenu]", recursive=False)
                for lvl1_cat in lvl1_cats:
                    if lvl1_cat.find("ul"):
                        lvl2 = lvl1_cat.find("ul", recursive=False)
                        lvl2_cats = lvl2.select("li[class^=navmenu]", recursive=False)
                        for lvl2_cat in lvl2_cats:
                            if lvl2_cat.find("ul"):
                                lvl3 = lvl2_cat.find("ul", recursive=False)
                                lvl3_cats = lvl3.select("li[class^=navmenu]", recursive=False)
                                for lvl3_cat in lvl3_cats:
                                    cat_link = lvl3_cat.find('a', href=True)['href']
                                    cat_link = domain + cat_link if domain not in cat_link else cat_link
                                    categories.append(cat_link)
                            else:
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
            print('Bove Spider: Failed to get Categories/ start urls')

        for cat_link in categories:
            yield scrapy.Request(cat_link, callback=self.parse, dont_filter=True)

    def parse(self, response):

        products = response.xpath('//div[@class="productitem"]').extract()
        for product in products:
            try:
                prod_soup = BS(product, "html.parser")
                external_link = prod_soup.find('a', {"class": "productitem--image-link"}, href=True)['href']
                if domain not in external_link:
                    external_link = domain + external_link

                yield scrapy.Request(external_link, callback=self.parse_product, dont_filter=True, meta={'external_link': external_link})

            except Exception as err:
                print(err)
                pass

            # break

        # follow next page links
        next_page = response.xpath('//nav[@class="pagination--container"]//li[@class="pagination--next"]//a/@href').extract()
        if next_page and next_page[0]:
            next_page_url = domain + next_page[0] if domain not in next_page[0] else next_page[0]
            yield scrapy.Request(url=next_page_url)

    def parse_product(self, response):
        external_link = response.meta.get('external_link')

        description = response.xpath('//meta[@property="og:description"]/@content').get() if response.xpath('//meta[@property="og:description"]/@content') else ''
        description = re.sub(r'[\r\n\t]+', ' ', description).strip().rstrip()

        script_divs = response.xpath("//script").getall()
        try:
            for div in script_divs:
                if 'data-section-id="static-product"' in div:
                    div_soup = BS(div, "html.parser").find('script')
                    if div_soup['data-section-id'] and div_soup['data-section-id'] == 'static-product':
                        data = json.loads(div_soup.contents[0])['product']
                        external_id = data['id']

                        external_category = data['type']

                        brand = data['vendor']

                        external_name = data['title']

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

                    break
        except Exception as err:
            print(err)
            return
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
