import re

import requests
from bs4 import BeautifulSoup
import csv

# 基础URL
base_url = "https://gr.xjtu.edu.cn"
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
info = {
    "学校": "",
    "学院": "",
    "姓名": "",
    "职称": "",
    "邮箱": [],
    "招生专业": "",
    "研究领域或研究方向": ""
}

# 提取信息
def extract_info(soup):
    if soup is None:
        return None

    # 提取职称
    title_tag = soup.find( string=re.compile( r'职称|教授|讲师' ) )
    if title_tag:
        info["职称"] = title_tag.strip()

    # 提取邮箱，处理不同的标签和格式
    email_patterns = [
        r'邮箱[:：]\s*([\w\.-]+@[\w\.-]+)',  # 匹配 "邮箱：" 格式
        r'<a href="mailto:([\w\.-]+@[\w\.-]+)">',  # 匹配 mailto 链接
        r'[\w\.-]+@[\w\.-]+'  # 通用邮箱匹配
    ]
    for pattern in email_patterns:
        emails = re.findall( pattern, str( soup.body ) )
        for email in emails:
            if email not in info["邮箱"]:
                info["邮箱"].append( email )

    # 提取研究领域或研究方向
    research_tag = soup.find( string=re.compile( r'研究领域|研究方向' ) )
    if research_tag:
        research_content = research_tag.find_next( 'p' ) or research_tag.find_next( 'div' )
        if research_content:
            info["研究领域或研究方向"] = research_content.get_text( strip=True )

    # 提取招生专业
    admission_tag = soup.find( string=re.compile( r'招生专业|招生方向|研究生招生' ) )
    if admission_tag:
        admission_content = admission_tag.find_next( 'p' ) or admission_tag.find_next( 'div' )
        if admission_content:
            info["招生专业"] = admission_content.get_text( strip=True )

    return info


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
        teachers = soup.select("a[href^='/web/']")
        # 遍历所有教师

        for teacher in teachers:
            teacher_url = base_url + teacher['href']
            response = requests.get(teacher_url,headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                name = teacher.get_text()
                profile_url = base_url + teacher['href']
                body_tag = soup.find( 'body' )
                extract_info(body_tag)


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
