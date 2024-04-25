from scrapy.exporters import JsonItemExporter
import MySQLdb


class EcommercePipeline:
	categories = {
		'Cameras & Drones': 1,
		'Computers & Peripherals': 2,
		'Health & Wellness': 3,
		'Hobbies, Books & Collections': 4,
		'Home & Living': 5,
		'Home Appliances': 6,
		'Miscellaneous': 7,
		'Mobile & Gadgets': 8,
		'Sports & Outdoors': 9,
		'Toys, Kids & Babies': 10,
		'Video Games': 11,
		'Watches': 12,
		'Uncategorized': 13
	}
	all_categories = {
		'Phones & Telecommunications': 8,
		'Computer, Office & Security': 2,
		'Consumer Electronics': 13,
		'Jewelry': 13,
		'Watches': 12,
		'Home, Pet & Appliances': 6,
		'Toys, Kids & Babies': 10,
		'Outdoor Fun & Sports': 9,
		'Electronics': 13,
		'Books': 4,
		'Home': 5,
		'Computer & Accessories': 2,
		'Camera & Photo': 1,
		'Health, Household & Personal Care': 3,
		'Baby': 10,
		'TV & Entertainment': 6,
		'IT & Mobile': 8,
		'Home Appliances': 6,
		'Kitchen Appliances': 5,
		'Health & Beauty Care': 3,
		'Fans & Air Care': 6,
		'Air Conditioners': 6,
		'Books & Magazines': 4,
		'Jewelry & Watches': 13,
		'Cameras & Photo': 1,
		'Video Games & Consoles': 11,
		'Movies & TV': 6,
		'Music': 4,
		'Cell Phones & Accessories': 8,
		'Computers/Tablets & Networking': 2,
		'Mobiles': 2,
		'Tablets': 2,
		'Laptops': 2,
		'Desktops Computers': 2,
		'Gaming Consoles': 2,
		'Action/Video Cameras': 1,
		'Security Cameras': 1,
		'Digital Cameras': 1,
		'Gadgets & Drones': 1,
		'Mobile Accessories': 8,
		'Audio': 8,
		'Wearables': 8,
		'Console Accessories': 11,
		'Camera Accessories': 1,
		'Computer Accessories': 2,
		'Storage': 2,
		'Printers': 2,
		'Computer Components': 2,
		'Network Components': 2,
		'TV & Video Devices': 6,
		'Home Audio': 6,
		'TV Accessories': 6,
		'Large Appliances': 6,
		'Small Kitchen Appliances': 6,
		'Cooling & Air Treatment': 6,
		'Vacuums & Floor Care': 6,
		'Personal Care Appliances': 3,
		'Parts & Accessories': 6,
		'Mother & Baby': 10,
		'Diapers & Wipes': 10,
		'Milk Formula & Baby Food': 10,
		'Nursing & Feeding': 10,
		'Baby Fashion & Accessories': 10,
		'Baby Gear': 10,
		'Bath & Baby Care': 10,
		'Maternity & Nursery': 10,
		'Toys & Games': 10,
		'Electronic & Remote Control Toys': 10,
		'Sports Toys & Outdoor Play': 9,
		'Baby & Toddler Toys': 10,
		'Men Watches': 12,
		'Women Watches': 12,
		'Kids Watches': 12,
		'Women Jewellery': 13,
		'Men Jewellery': 13,
		'Sunglasses': 13,
		'Contact Lenses': 13,
		'Eyeglasses': 13,
		'Women Bags': 13,
		'Men Bags': 13,
		'Travel': 13,
		'Kids Bags': 13,
		'Computers & Tech': 2,
		'Mobile Phones & Gadgets': 8,
		'Luxury': 13,
		'Video Gaming': 11,
		'Photography': 1,
		'TV & Home Appliances': 6,
		'Babies & Kids': 10,
		'Hobbies & Toys': 10,
		'Health & Nutrition': 3,
		'Cameras & Drones': 1,
		'Computers & Peripherals': 2,
		'Health & Wellness': 3,
		'Hobbies, Books & Collections': 4,
		'Home & Living': 5,
		'Miscellaneous': 7,
		'Mobile & Gadgets': 8,
		'Sports & Outdoors': 9,
		'Video Games': 11
	}

	def open_spider(self, spider):
		"""spider_name = spider.name
		file_path_producer = f'{spider.settings.get("DATA_FILE_PATH")}/{spider_name}.json'
		self.file = open(file_path_producer, 'wb')
		self.exporter = JsonItemExporter(self.file, encoding='utf-8')
		self.exporter.start_exporting()"""

		host = "52.221.189.97"
		user = "pricegiraff"
		password = "UKVtEBZQP7hTf3HH"
		port = 3306
		self.con = MySQLdb.connect(host=host, user=user, password=password, port=port, charset='utf8')
		self.cur = self.con.cursor()
		self.cur.execute('create database if not exists ecommerce_data')
		self.con.select_db('ecommerce_data')
		self.create_tables()

		# Insert the site
		site_id = spider.site_id
		site_name = spider.site_name
		site_url = spider.site_url
		site_favicon = spider.site_favicon
		logo = spider.logo
		self.cur.execute("""INSERT IGNORE INTO site VALUES (%s,%s,%s,%s,%s)""", (site_id, site_name, site_url, site_favicon, logo))

		# Create the categories
		for cat in self.categories:
			cat_id = self.categories[cat]
			self.cur.execute("""INSERT IGNORE INTO category VALUES (%s,%s)""", (cat_id, cat))

		self.con.commit()

	def close_spider(self, spider):
		"""self.exporter.finish_exporting()
		self.file.close()"""

		self.con.commit()
		self.cur.close()
		self.con.close()

	def create_tables(self):
		# Site table
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS site(
				id int not null primary key,
				name varchar(100),
				url varchar(100),
				favicon varchar(100)
			)
		""")
		# Category table
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS category(
				id int not null primary key,
				name varchar(100)
			)
		""")
		# Product table
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS product(
				id varchar(100) not null primary key,
				site_id int,
				category_id int,
				extrenal_category varchar(100),
				external_link varchar(300) not null unique,
				external_name varchar(400) not null,
				description text not null,
				brand varchar(200) null,
				external_id varchar(30),
				sold int,
				last_updated timestamp,
				foreign key (site_id) references site(id),
				foreign key (category_id) references category(id)
			)
		""")
		# Image table
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS image(
				product_id varchar(100) not null,
				link varchar(300),
				is_thumbnail int(1) default 0,
				foreign key (product_id) references product(id),
				primary key (product_id, link)
			);
		""")
		# Model table
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS model(
				id varchar(100) not null primary key,
				external_id varchar(30),
				name varchar(400) not null,
				image varchar(100),
				last_price double,
				product_id varchar(100) not null,
				foreign key (product_id) references product(id)
			);
		""")
		# History table
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS history(
				model_id varchar(100),
				scraped_date timestamp,
				price double,
				foreign key (model_id) references model(id),
				primary key (model_id, scraped_date)
			)
		""")

	def process_item(self, item, spider):
		try:
			cat_id = self.all_categories[item["external_category"]]
		except:
			cat_id = 13
		id_cur = f'{spider.name}_{item["external_id"]}'
		item['description'] = "".join(c for c in item['description'] if ord(c) < 128)
		item['external_name'] = item['external_name'].replace('?', '"')
		item['external_name'] = "".join(c for c in item['external_name'] if ord(c) < 128)
		item['external_link'] = item['external_link'].replace('%3A', ':').replace('%3F', '?').replace('%3D', '=')
		sold = item['Sold'] if 'Sold' in item else ''
		if sold:
			self.cur.execute("""INSERT INTO product VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,current_timestamp(),NULL) ON DUPLICATE KEY UPDATE last_updated=current_timestamp(), category_id=%s, sold=%s""", (id_cur, spider.site_id, cat_id, item["external_category"], item['external_link'], item['external_name'], item['description'], item['brand'], item['external_id'], sold, cat_id, sold))
		else:
			self.cur.execute("""INSERT INTO product VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,current_timestamp(),NULL) ON DUPLICATE KEY UPDATE last_updated=current_timestamp(), category_id=%s""", (id_cur, spider.site_id, cat_id, item["external_category"], item['external_link'], item['external_name'], item['description'], item['brand'], item['external_id'], cat_id))
		self.con.commit()
		for model in item['models']:
			model_id = f'{id_cur}_{model["external_id"]}'
			model['name'] = model['name'].replace('?', '"')
			model['name'] = "".join(c for c in model['name'] if ord(c) < 128)
			model['price'] = float(str(model['price']).replace(',', ''))
			self.cur.execute("""INSERT INTO model VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE last_price=%s""", (model_id, model['external_id'], model['name'], "", model['price'], id_cur, model['price']))
			self.con.commit()
		is_thumbnail = 1
		for image in item['images']:
			if image:
				self.cur.execute("""INSERT IGNORE INTO image VALUES (%s,%s,%s)""", (id_cur, image, is_thumbnail))
				is_thumbnail = 0
		self.con.commit()
		# self.exporter.export_item(item)
		return item
