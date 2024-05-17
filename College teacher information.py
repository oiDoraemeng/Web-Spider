import re

import requests
from bs4 import BeautifulSoup
import csv

# 基础URL
base_url = "https://gr.xjtu.edu.cn"
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
# 获取所有学院的URL
def get_college_urls():

    url ='https://gr.xjtu.edu.cn/college-list'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 选择器：选择所有以'/web/'开头的链接
    links = soup.select("a[href^='https://gr.xjtu.edu.cn/college-list?']")
    college_urls = [link['href'] for link in links]
    return college_urls

# 获取指定学院的教师信息
def get_teacher_info(college_url):
    response = requests.get(college_url,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 选择器：选择网页所有的教师页数
    # 使用正则表达式匹配href属性中包含'cur='后跟数字的<a>标签
    page_links = soup.find_all('a', href=re.compile(r'cur=\d+'))

    # 遍历所有教师页数
    for page_link in page_links:
        page_url=page_link['href']
        response = requests.get(page_url,headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 选择器：选择教师列表中的所有链接
        teachers = soup.select(".teacher_list a")
        teacher_info = []
        for teacher in teachers:
            name = teacher.get_text()
            profile_url = base_url + teacher['href']
            teacher_info.append((name, profile_url))
        return teacher_info

# 主程序
def main():
    colleges = get_college_urls()
    all_teachers = []
    for college in colleges:
        teachers = get_teacher_info(college)
        all_teachers.extend(teachers)

    # 将数据保存到CSV文件
    with open('teachers_info.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['姓名', '个人主页URL'])
        writer.writerows(all_teachers)

if __name__ == "__main__":
    main()
