from ecommerce.spiders.base_spider import BaseSpider
from datetime import datetime
from bs4 import BeautifulSoup
import cloudscraper
import regex
import json


class Spider(BaseSpider):
    name = 'gaincity'
    scraper = ''
    start_urls = ['https://shopee.sg/']

    site_id = 8
    site_name = 'Gain City'
    site_url = 'https://www.gaincity.com'
    site_favicon = 'https://www.gaincity.com/pub/media/favicon/stores/1/favicon-32x32_1.png'
    logo = 'https://www.gaincity.com/pub/media/logo/stores/1/gc-logo.png'

    def parse(self, response):
        while True:
            try:
                self.scraper = cloudscraper.create_scraper()
                r = self.scraper.get('https://www.gaincity.com')
                soup = BeautifulSoup(r.text, 'lxml')
                categories = soup.find_all('ul')[1].find_all('a', class_='level-top')
                print('NICE')
                break
            except:
                print('FAILED')
                continue
        for category in categories:
            external_category = category.text
            category = category['href']
            r = self.scraper.get(category)
            soup = BeautifulSoup(r.text, 'lxml')
            sub_categories = [category]
            if any(x in category for x in ['air-conditioners', 'vision&audio']):
                sub_categories = [x['href'] for x in soup.find('div', class_='row text-center gc-microsite-logo').find_all('a', class_='block')]
            elif any(x in category for x in ['servicing', 'furniture']):
                sub_categories = [x['href'] for x in soup.find_all('a', class_="block")]
            for link in sub_categories:
                p = 0
                while True:
                    p += 1
                    extension = '?p=' + str(p) if '?' not in link else '&p=' + str(p)
                    l = link + extension if 'https://' in link else 'https://www.gaincity.com/' + link + extension
                    r = self.scraper.get(l)
                    soup = BeautifulSoup(r.text, 'lxml')
                    products = soup.find_all('div', class_='product-item-info')
                    for product in products:
                        try:
                            status = soup.find_all('div', class_='product-item-info')[0].find('div', class_='stock').text
                            if status == 'Out of stock':
                                continue
                        except:
                            pass
                        external_link = product.find('a', class_='product-item-link')['href']
                        r = self.scraper.get(external_link)
                        soup = BeautifulSoup(r.text, 'lxml')
                        external_name = soup.find('span', class_='base').text
                        model_name = soup.find('div', class_='product attribute model').text.replace('Model', '').strip()
                        scraping_date = datetime.today()
                        brand = soup.find('div', class_='brand-view').find('a')['title'] if soup.find('div', class_='brand-view').find('a') else ''
                        external_id = soup.find('div', class_='price-box')['data-product-id'] if soup.find('div', class_='price-box') else '0'
                        description = soup.find('meta', itemprop='description')['content'] if soup.find('meta', itemprop='description') else ''
                        price = soup.find('span', class_='price').text.strip('$').replace(',', '')

                        models = [{
                            'external_id': external_id,
                            'name': model_name,
                            'description': description,
                            'price': price
                        }]
                        pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}')
                        possibilities = pattern.findall(r.text)
                        for item in possibilities:
                            if '"type":"image"' in item:
                                jsonText = item
                                break
                        images = []
                        if jsonText:
                            jsonData = json.loads(jsonText)
                            for image in jsonData['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']:
                                image_src = image['full']
                                images.append(image_src)

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
                    if len(products) < 40:
                        break