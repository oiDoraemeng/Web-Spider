import requests
from lxml import etree
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient
from login import login

# 连接MongoDB数据库
client = MongoClient('mongodb://192.168.1.11:27017/')

# MongoDB 中可存在多个数据库，根据数据库名称获取数据库对象
db = client.movie



PHONE = "15926159067"
base_url = "https://movie.douban.com"

COOKIES = login(PHONE)
headers = {
    'Cookies': COOKIES,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}
url = "https://movie.douban.com/chart"
response = requests.get(url, headers=headers)
html = etree.HTML(response.text)
movies_type = html.xpath('//a[contains(@href, "/typerank?type_name=")]')

def tranInfodist(infos):
    infos_dist = {}
    infos = [item for item in infos if item != ''and item!= "        "]
    for info in infos:
        try:
            # if "：" in info:  # 处理中文冒号
            #     key, value = info.split("：",1)
            # else:  # 处理英文冒：
            key, value = info.split(":", 1)
            infos_dist[key.strip()] = value.strip()
        except ValueError:
            print("错误：{}字符串中没有冒号".format(info))
    return infos_dist

def get_movies_info(json_data):
    """
    movies_info={
        "电影": "",
        "海报": "",
        "导演": "",
        "编剧": "",
        "主演": "",
        "类型": "",
        "制片国家/地区": "",
        "语言": "",
        "上映日期": "",
        "片长": "",
        "又名": "",
        "IMDb链接": "",
        "评分": "",
        "评价人数": "",
        "简介": ""
        "豆瓣链接": "",
    }

    """

    for item in json_data:
        movie_info = {}
        movie_url = item.get("url", "")
        response_movie = requests.get(movie_url, headers=headers)
        if response_movie.status_code != 200:
            print(f"{movie_url}发生重定向")
            continue
        html_movie = etree.HTML(response_movie.text)
        infos = html_movie.xpath('//div[@id="info"]')[0].xpath('string()').split('\n')

        infodist = tranInfodist(infos)

        movie_info["电影"] = item.get("title","")
        movie_info["海报"] = item.get("cover_url","")
        movie_info["导演"] = infodist.get("导演","")
        movie_info["编剧"] = infodist.get("编剧","")
        movie_info["主演"] = "/".join(item.get("actors",""))
        movie_info["类型"] = "/".join(item.get("types",""))
        movie_info["制片国家/地区"] = "/".join(item.get("regions",""))
        movie_info["语言"] = infodist.get("语言","")
        movie_info["上映日期"] = infodist.get("上映日期","")
        movie_info["片长"] = infodist.get("片长","")
        movie_info["又名"] = infodist.get("又名","")
        movie_info["IMDb链接"] = infodist.get("IMDb","")
        movie_info["评分"] = item["score"]
        movie_info["评价人数"] = item["vote_count"]
        summary = html_movie.xpath('//span[@property="v:summary"]')
        movie_info["简介"] = summary[0].text.strip() if summary else ""
        movie_info["豆瓣链接"] = item.get("url","")
        collection.insert_one(movie_info)



for M_type in movies_type:
    print(M_type.get("href"))
    parsed_url = urlparse(M_type.get("href"))
    query_string = parsed_url.query
    parsed_query = parse_qs(query_string)
    collection = db[parsed_query["type_name"][0]]
    url_conunt = "https://movie.douban.com/j/chart/top_list_count"
    params = {
        "type": parsed_query["type"][0],
        "interval_id": parsed_query["interval_id"][0],
        "action": ""
    }
    response_count = requests.get(url_conunt, params=params, headers=headers)
    print(response_count.json())

    url_list = "https://movie.douban.com/j/chart/top_list"
    params = {
        "type": parsed_query["type"][0],
        "interval_id": parsed_query["interval_id"][0],
        "action": "",
        "start": "0",
        # "limit": "2"
        "limit": str(response_count.json()["total"])
    }
    response_list = requests.get(url_list, params=params, headers=headers)
    print(response_list.json())
    get_movies_info(response_list.json())


