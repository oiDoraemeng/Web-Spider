import json
import re
import json

import requests

from bs4 import BeautifulSoup
import csv
from urllib.parse import unquote

from zhipuai import ZhipuAI

import jieba
wenxi_url = 'https://luckycola.com.cn/aliai/tyqw'

# 基础URL
base_url = "https://gr.xjtu.edu.cn"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}
infolist = []


def get_keywords_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    keywords = set()
    for college in data['学院'].values():
        keywords.update(college['专业'])
        keywords.update(college['研究方向'])

    for discipline in data['学科'].values():
        keywords.update(discipline['专业'])
        keywords.update(discipline['研究方向'])
        keywords.update(discipline['院系'])

    return keywords

def get_college_name(soup):
    # 查找包含“版权”的标签
    copyright_tag = soup.find(lambda tag: tag.string and '版权' in tag.string)

    if copyright_tag:
        # 打印找到的标签
        print(copyright_tag)

        # 提取大学名字
        text = copyright_tag.get_text()
        university_name = None

        # 使用正则表达式匹配冒号后面不含冒号的内容
        match = re.search(r'[:：]\s*([^:：\s]+)', text)
        if match:
            university_name = match.group(1)
            return university_name
        else:
            print("未找到大学名称")


# 提取信息
def get_info(soup,info):
    if soup is None:
        return None
    body = soup.body

    # 定位到包含特定标题的 div
    def find_section_div(title= None):
        if title :
            header = body.find('h2', {'title': title})
            if header:
                return header.find_parent('div', class_='portlet-content').get_text()

        tags = body.find_all('div', class_='portlet-body')
        texts = [tag.get_text() for tag in tags]
        return " ".join(texts)

    result = []
    email_patterns = [
        r'邮箱[:：\s]*([\w\.-]+@[\w\.-]+)',  # 匹配 "邮箱：" 格式
        r'<a href="mailto:([\w\.-]+@[\w\.-]+)">',  # 匹配 mailto 链接
        r'[\w\.-]+@[\w\.-]+'  # 通用邮箱匹配
    ]
    # 提取联系方式中的邮箱，并屏蔽网页末端的邮箱
    contact_info_div = find_section_div('联系方式')
    if contact_info_div:
        for pattern in email_patterns:
            emails = re.findall(pattern, contact_info_div)
            for email in emails:
                if email not in result:
                    result.append(email)


    # 提取基本信息中的职称
    # 匹配包含职称关键字的部分
    title_pattern = re.compile(
        r'(教授|讲师|博士生导师|副教授|研究员|副研究员|助教|讲师助理|副教授助理|教授助理|博士生导师助理|副研究员助理|研究员助理)')
    pattern = re.compile(r'(信息|个人信息|个人简介|基本信息)')
    tags = body.find_all('h2', class_='portlet-title-text')
    text= ""
    for tag in tags:
        text = pattern.findall(tag.get_text())
        break
    basic_info_div = find_section_div("".join(text))
    if basic_info_div:
        titles = title_pattern.findall(basic_info_div)
        if titles:
            for pattern in email_patterns:
                emails = re.findall(pattern, basic_info_div)
                for email in emails:
                    if email not in result:
                        result.append(email)
            result = [x for x in result if x!="xjtuteacher@mail.xjtu.edu.cn"]
            info["职称"] = ' '.join(titles)
            info["邮箱"] = " ".join(result)

    # tags = soup.find_all('h2', class_='portlet-title-text')
    # texts = [tag.get_text() for tag in tags]
    # texts = [x for x in texts if x != '基本信息' and x != '联系方式']
    # # 提取研究领域或研究方向（假设研究方向在剩下的两类中）
    # research_info_div = find_section_div('研究方向') or find_section_div('研究领域')
    # if research_info_div:
    #     research_content = research_info_div.find_next('p') or research_info_div.find_next('div')
    #     if research_content:
    #         info["研究领域或研究方向"] = research_content.get_text(strip=True)
    #
    # # 提取招生专业
    # admission_info_div = find_section_div('招生专业')
    # if admission_info_div:
    #     admission_content = admission_info_div.find_next('p') or admission_info_div.find_next('div')
    #     if admission_content:
    #         info["招生专业"] = admission_content.get_text(strip=True)

    client = ZhipuAI(api_key="731f9a8e7fe667944fbbee831cf574b7.9pbaB8x2GlFRQeVR")  # 填写您自己的APIKey

    result = ""
    div_text = find_section_div()
    result =div_text.replace('\n', '').replace('\r', '').replace(' ', '')


    with open(r'config.json', 'rb') as file:
        data = json.load(file)
    if result:
        if info["研究领域或研究方向"] == "":
            ques = "根据以上信息，总结出研究领域或者现在最新研究方向，（简洁明了，20字以内，如果文本为英文，请翻译后在分析）" + result
            data["body"]["ques"] = ques
            # 将字典转换为JSON格式的字符串
            # body_json = json.dumps(data["body"])
            # # 发送POST请求
            # response = requests.post(wenxi_url, data= body_json, headers={'Content-Type': 'application/json'})
            # info["研究领域或研究方向"] = response.text

            response = client.chat.completions.create(
                model="glm-4",  # 填写需要调用的模型名称
                messages=[{"role": "user", "content": ques}, ]
            )
            info["研究领域或研究方向"] = response.choices[0].message.content
        if result :
            if info["招生专业"] == "":
                ques = "根据信息，找出招生专业，或者总结最新招生专业，（至少一个,10字以内，用空格隔开，如果文本为英文，请翻译后在分析）:" + ' '.join(result)
                data["body"]["ques"] = ques
                # # 将字典转换为JSON格式的字符串
                # body_json = json.dumps(data["body"])
                # # 发送POST请求
                # response = requests.post(wenxi_url, data=body_json, headers={'Content-Type': 'application/json'})
                # info["招生专业"] = response.text

                response = client.chat.completions.create(
                    model="glm-4",  # 填写需要调用的模型名称
                    messages=[{"role": "user", "content": ques}, ]
                )
                info["招生专业"] = response.choices[0].message.content

                print(info)
                with open('teachers_info.csv', mode='a', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file,quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow([info["学校"], info["学院"], info["姓名"], info["职称"], info["邮箱"], info["招生专业"], info["研究领域或研究方向"], info["个人主页"]])
                    file.close()
    return info


def get_college_urls(keywords):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # college_urls = {}
    # url = 'https://gr.xjtu.edu.cn/college-list'
    # # 设置ChromeOptions # 忽略证书错
    # chrome_options = Options()
    # chrome_options.add_argument('--ignore-certificate-errors')

    # # 启动Chrome浏览器
    # driver = webdriver.Chrome()
    #
    # driver.get(url)
    #
    # # 找到所有学院的链接
    # college_links = driver.find_elements_by_css_selector('a[href^="https://gr.xjtu.edu.cn/college-list?"]')
    #
    # # 循环点击每个学院链接，并获取完整的URL
    # for link in college_links:
    #     link.click()
    #     # 等待页面加载
    #     driver.implicitly_wait(5)
    #     # 获取当前页面的URL
    #     current_url = driver.current_url
    #     # 提取学院名称作为键，完整URL作为值，添加到字典中
    #     college_name = link.text
    #     college_urls[college_name] = current_url
    #     # 返回到学院列表页面
    #     driver.back()
    #
    # # 关闭浏览器
    # driver.quit()
    #
    # return college_urls

    college_urls = {}
    url = 'https://gr.xjtu.edu.cn/college-list'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser', from_encoding='utf-8')
    # 选择器：选择所有以'/web/'开头的链接
    links = soup.select("a[href^='https://gr.xjtu.edu.cn/college-list?']")

    # 对列表中的每个元素进行分词
    keywords_segments = [jieba.cut(word, cut_all=False) for word in list(keywords)]
    # 将分词结果合并为一个列表
    keywords_words = [word for segment in keywords_segments for word in segment]
    # 过滤掉停用词
    stopwords = [line.strip() for line in open("stopwords.txt", 'r', encoding='utf-8').readlines()]
    keywords_words = [word for word in keywords_words if word not in stopwords]
    # 词频统计
    word_freq = {}
    for word in keywords_words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    # 筛选出词频最高的三个关键词
    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
    for link in links:
        college_name = link.get_text()

        # 选出包含关键词的学院
        if any(word in college_name for word in keywords_words):
            # 解码URL
            link = unquote(link['href'])
            # 检查是否已经存在相同的学院名字
            if college_name in college_urls:
                # 查找一个唯一的名字
                counter = 2
                new_college_name = f"{college_name} ({counter})"
                while new_college_name in college_urls:
                    counter += 1
                    new_college_name = f"{college_name} ({counter})"
                college_urls[new_college_name] = link
            else:
                college_urls[college_name] = link

    return college_urls


# 获取指定学院的教师信息
def get_teacher_urls(college_urls):
    teachers_urls = {}
    for college_name, college_url in college_urls.items():
        # 创建会话对象
        session = requests.Session()
        response = session.get(college_url, headers=headers)
        # response = requests.get(college_url,headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 选择器：选择网页所有的教师页数
        # 使用正则表达式匹配href属性中包含'cur='后跟数字的<a>标签
        page_links = soup.find_all('a', href=re.compile(r'cur=\d+'))

        # 用于跟踪已看到的cur值
        seen_curs = set()
        unique_page_links = []

        for link in page_links:
            # 提取cur值
            match = re.search(r'cur=(\d+)', link['href'])
            if match:
                cur_value = match.group(1)
                if cur_value not in seen_curs:
                    seen_curs.add(cur_value)
                    unique_page_links.append(link)

        teachers_urls[college_name]=[]
        # 遍历所有教师页数
        for page_link in unique_page_links:
            # 解码URL
            page_link = unquote(page_link['href'])
            # 请求教师页
            headers1 = {
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
            }
            # 请求教师页
            response = session.get(page_link, headers=headers1)
            # response = requests.get(page_link)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select("a[href^='/web/']")
            teachers_urls[college_name].extend(links)
            print(college_name, page_link)

        # break
    return teachers_urls


def get_teacher_info(teachers_urls):

    for college_name, teachers in teachers_urls.items():
        for teacher in teachers:
            info = {
                "学校": "",
                "学院": "",
                "姓名": "",
                "职称": "",
                "邮箱": "",
                "招生专业": "",
                "研究领域或研究方向": "",
                "个人主页": ""
            }
            teacher_url = base_url + teacher['href']
            response = requests.get(teacher_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                info["学校"] = get_college_name(soup)
                info["学院"] = college_name
                info["姓名"] = teacher.get_text()
                info["个人主页"] = base_url + teacher['href']
                infolist.append(get_info(soup,info))

    return infolist
# 主程序
def main():

    with open('teachers_info.csv', mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["学校", "学院", "姓名", "职称", "邮箱", "招生专业", "研究领域或研究方向", "个人主页"])
        file.close()
    # 读取JSON文件并提取关键词
    json_file = 'config.json'
    keywords = get_keywords_from_json(json_file)
    colleges_urls = get_college_urls(keywords)
    teachers_urls = get_teacher_urls(colleges_urls)
    get_teacher_info(teachers_urls)



if __name__ == "__main__":
    main()
