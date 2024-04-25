from ecommerce.spiders.base_spider import BaseSpider
from datetime import datetime
import requests
import scrapy
from bs4 import BeautifulSoup

class Spider(BaseSpider):
    name = 'qoo10'
    start_urls = ['https://www.qoo10.sg/']
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0"}

    site_id = 10
    site_name = 'Qoo10'
    site_url = 'https://www.qoo10.sg'
    site_favicon = 'https://www.qoo10.sg/favicon.ico'
    logo = 'https://upload.wikimedia.org//wikipedia/en/thumb/4/41/Qoo10_Logo_2018.png/220px-Qoo10_Logo_2018.png'
    category_api = "https://www.qoo10.sg/gmkt.inc/Category/DefaultAjaxAppend.aspx"

    def parse(self, response):
        for categoryID in ['4', '5', '10']:
            r = requests.get(f'https://www.qoo10.sg/gmkt.inc/Category/Group.aspx?g={categoryID}', headers=self.headers)
            soup = BeautifulSoup(r.text, 'lxml')
            for sub_category_url in [x.find('a')['href'] if x.find('a') else '' for x in soup.find_all('h2', class_="cate_tt")]:
                if sub_category_url == '':
                    continue
                r = requests.get(sub_category_url, headers=self.headers)
                soupz = BeautifulSoup(r.text, 'lxml')
                page_n = 0
                c_url = sub_category_url
                while True:
                    page_n += 1
                    querystring = {"p":str(page_n),"s":"r","v":f"g{categoryID}","ct":c_url.split('=')[-1],"f":f"st:SG|ct:{c_url.split('=')[-1]}|","t":"gc"}
                    r = requests.request("POST", self.category_api, headers=self.headers, params=querystring)
                    soup = BeautifulSoup(r.text, 'lxml')
                    items = soup.find_all('div', class_='item')
                    if not items:
                        break
                    n = 0
                    for item in items:
                        product_url = item.find('a', class_='thmb')['href']
                        yield scrapy.Request(product_url, headers=self.headers, callback=self.parse_product_1, dont_filter=True)
                    try:
                        if (int(soupz.find('h3', id='h_filter_header_title').find('strong').text.replace(',', '')) // 100 + 1) == page_n:
                            break
                    except:
                        pass

    def parse_product_1(self, response):
        external_category = response.xpath('//span[@itemprop="name"]/text()').getall()[1]
        external_name = response.xpath('//h2[@id="goods_name"]/text()').get()
        external_id = response.xpath('//div[@class="code"]/text()').getall()[1].replace(':', '').strip().rstrip()
        external_link = response.url
        brand = response.xpath('//div[@class="goods-detail__brand"]/a/mark/text()').get()
        brand = brand.strip('[]') if brand else ''
        brand = response.xpath('//span[@id="btn_brand"]/text()').get() if not brand else brand
        inventory_number = response.xpath('//input[@id="inventory_no"]/@value').get().strip()
        base_price = response.xpath('//div[@class="prc"]/strong/@data-price').get()
        base_price = response.xpath('//strong[@id="qprice_span"]/@data-price').get() if not base_price else base_price
        base_price = float(base_price)
        images = []
        for url in response.xpath('//img[contains(@id, "ImgIndicateID")]/@src').getall():
            if 'youtube.com' not in url:
                images.append(url.replace('g_80', 'g_520'))
        try:
            r = requests.get(f'https://www.qoo10.sg/gmkt.inc/Goods/GoodsDetailOriginal.aspx?__ar=Y&goodscode={external_id}&from=gdetail&contents_no=0&global_order_type=L', headers=self.headers)
            soup = BeautifulSoup(r.text, 'lxml')
            description = '\n'.join([x.text for x in soup.find_all('p')])
            scraping_date = datetime.today()

            url = "https://www.qoo10.sg/gmkt.inc/swe_GoodsAjaxService.asmx/GetGoodsInventoryEachLevelName"
            payload = {
                "inventory_no": inventory_number,
                "sel_value1":"",
                "sel_value2":"",
                "sel_value3":"",
                "sel_value4":"",
                "level": 1,
                "sel_count": 99,
                "lang_cd": "en",
                "global_order_type": "L",
                "gd_no": external_id,
                "inventory_yn": "",
                "link_type": "N"
            }
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0","Referer": external_link}

            modelsJson = requests.request("POST", url, json=payload, headers=headers).json()
            models = []
            prims = []
            secs = []
            for model in modelsJson['d']:
                primary_model = model['sel_value']
                prims.append(primary_model)
                primary_model_price = model['min_inv_price'] if model['min_inv_price'] and model['min_inv_price'] > 0 else 0
                sel_no = model['sel_no']
                payload['sel_value1'] = primary_model
                models.append([sel_no, primary_model, base_price + primary_model_price])
                modelsJson = requests.request("POST", url, json=payload, headers=headers).json()
                for sec_model in modelsJson['d']:
                    secondary_model = sec_model['sel_value']
                    if secondary_model in prims:
                        break
                    secs.append(secondary_model)
                    secondary_model_price = sec_model['min_inv_price'] if sec_model['min_inv_price'] and sec_model['min_inv_price'] > 0 else 0
                    sel_no = sec_model['sel_no']
                    models.append([sel_no, primary_model + ', ' + secondary_model, base_price + primary_model_price + secondary_model_price])
                    payload['sel_value2'] = secondary_model
                    models.append([sel_no, primary_model + ', ' + secondary_model, base_price + primary_model_price + secondary_model_price])
            if not models:
                models.append([external_id, external_name, base_price])

            models_data = [{
                    'external_id': model[0],
                    'name': model[1],
                    'description': '',
                    'price': model[2]
                    } for model in models]

            yield {
                'external_category': external_category,
                'external_link': external_link,
                'external_name': external_name,
                'description': description,
                'brand': brand,
                'external_id': external_id,
                'scraping_date': scraping_date,
                'models': models_data,
                'images': images
            }
        except Exception as err:
            print(err)