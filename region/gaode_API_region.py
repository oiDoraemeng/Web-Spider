import requests
import csv

# 替换为你自己的高德地图API Key
api_key = '888c59c6be876c8857894ef20e473e67'

# 指定要查询的市区（可以根据具体需求调整参数）
city = '湘西土家族苗族自治州'

# 高德地图行政区划查询API URL
district_url = f'https://restapi.amap.com/v3/config/district'
params = {
    'key': api_key,
    'keywords': city,
    'subdistrict': 4,
    'page':1
}

# 发起请求获取行政区划信息
response = requests.get(district_url, params=params)
district_data = response.json()

county = []

# 确保请求成功并获取到了行政区划信息
if district_data['status'] == '1':
    county_districts = district_data['districts'][0]['districts']

    with open('villages.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 遍历行政区划信息，收集自然村信息
        for county_district in county_districts:
            county.append(county_district['name'])
            writer.writerow([county_district['name']])
            # 遍历行政区划信息，收集街道信息
            street_districts = county_district['districts']
            street = []
            for street_district in street_districts:
                street.append(street_district['name'])

            writer.writerow(street)
        # 将自然村信息保存到CSV文件
        print("自然村信息已保存至villages.csv")
else:
    print("无法获取行政区划信息，错误信息:", district_data['info'])
