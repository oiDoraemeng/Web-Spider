import requests
import csv
from lxml import etree
import uuid

class Node:
    def __init__(self, name, url=None, parent_id=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.url = url
        self.parent_id = parent_id

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            # "url": self.url,
            "parent_id": self.parent_id
        }


# base_url = "https://www.stats.gov.cn/sj/tjbz/tjyqhdmhcxhfdm/2023/43/4331.html"
# response = requests.get(base_url)
# response.encoding = 'utf-8'
# html = etree.HTML(response.text)
# county= html.xpath('//tr[@class="countytr"]/td[2]/a')
# with open('villages.csv', 'w', newline='', encoding='utf-8-sig') as file:
#     writer = csv.writer(file)
#     for a in county:
#         writer.writerow([a.text])
#         county_url=base_url.split('4331.html')[0]+a.get('href')
#         print(county_url)
#         response = requests.get(county_url)
#         response.encoding = 'utf-8'
#         html = etree.HTML(response.text)
#         town = html.xpath('//tr[@class="towntr"]/td[2]/a')
#         for b in town:
#             writer.writerow([b.text])
#             town_url=county_url.split(county_url.split('/')[-1])[0]+b.get('href')
#             print(town_url)
#             response = requests.get(town_url)
#             response.encoding = 'utf-8'
#             html = etree.HTML(response.text)
#             village = html.xpath('//tr[@class="villagetr"]/td[3]')
#             village = [i.text for i in village]
#             writer.writerow(village)
#
#

def crawl_data(base_url):
    response = requests.get(base_url)
    response.encoding = 'utf-8'
    html = etree.HTML(response.text)
    root = Node('湘西土家族苗族自治州')

    nodes = [root]

    county_elements = html.xpath('//tr[@class="countytr"]/td[2]/a')
    for county_elem in county_elements:
        county_name = county_elem.text
        county_url = base_url.split('4331.html')[0] + county_elem.get('href')
        print(county_name, county_url)
        county_node = Node(county_name, county_url, root.id)
        nodes.append(county_node)

        county_response = requests.get(county_url)
        county_response.encoding = 'utf-8'
        county_html = etree.HTML(county_response.text)

        town_elements = county_html.xpath('//tr[@class="towntr"]/td[2]/a')
        for town_elem in town_elements:
            town_name = town_elem.text
            town_url = county_url.split(county_url.split('/')[-1])[0] + town_elem.get('href')
            print(town_name, town_url)
            town_node = Node(town_name, town_url, county_node.id)
            nodes.append(town_node)

            town_response = requests.get(town_url)
            town_response.encoding = 'utf-8'
            town_html = etree.HTML(town_response.text)

            village_elements = town_html.xpath('//tr[@class="villagetr"]/td[3]')
            for village_elem in village_elements:
                village_name = village_elem.text
                village_node = Node(village_name, parent_id=town_node.id)
                nodes.append(village_node)

    return nodes

base_url = "https://www.stats.gov.cn/sj/tjbz/tjyqhdmhcxhfdm/2023/43/4331.html"
nodes = crawl_data(base_url)

from pymongo import MongoClient

client = MongoClient('mongodb://192.168.1.12:27017/')
db = client['mydatabase']
collection = db['region']

# 清空集合
collection.delete_many({})

# 插入数据
for node in nodes:
    collection.insert_one(node.to_dict())

