import random
import re
import os
import cv2
import time

import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pymongo import MongoClient

from function import get_slider_captcha_contour

# 获取代理IP
ip_url = "http://api.shenlongip.com/ip?key=d9thmms4&pattern=txt&count=1&mr=1&protocol=1&sign=7234adf2be22e5b8be06c471d2b68026"
response = requests.get(ip_url)
proxy = response.text
proxy = proxy.strip()  # 去除换行符和空格

# iplist = []
# with open("ip.txt") as f:
#     iplist = f.readlines()
#
#
# # 获取ip代理
# def getip():
#     proxy = iplist[random.randint(0, len(iplist) - 1)]
#     proxy = proxy.strip()  # 去除换行符和空格
#     # proxies={
#     #     'http':'http://'+str(proxy),
#     #     #'https':'https://'+str(proxy),
#     # }
#     return proxy


# 连接MongoDB数据库
client = MongoClient('mongodb://192.168.1.11:27017/')

# MongoDB 中可存在多个数据库，根据数据库名称获取数据库对象
db = client.mydatabase

# 指定集合
collection = db.movies
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


def scrolled_to_bottom(driver):
    # # 获取页面总高度
    # last_height = driver.execute_script("return document.body.scrollHeight")
    #
    # while True:
    #     # 模拟滚动到底部
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #
    #     # 等待加载更多内容
    #     time.sleep(random.uniform(3, 5))  # 根据实际情况调整等待时间
    #
    #     # 计算新的页面高度
    #     new_height = driver.execute_script("return document.body.scrollHeight")
    #
    #     # 检查是否已滚动到底部
    #     if new_height == last_height:
    #         break
    #     last_height = new_height

    # 初始加载的元素数量
    initial_count = len(driver.find_elements(By.CSS_SELECTOR, ".movie-list-item.playable.unwatched"))

    while True:
        # 模拟滚动到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        try:
            # 等待新元素加载
            WebDriverWait(driver, 10).until(
                lambda driver: len(
                    driver.find_elements(By.CSS_SELECTOR, ".movie-list-item.playable.unwatched")) > initial_count
            )
        except TimeoutException:
            # 如果超时，认为没有更多内容加载
            break

        # 更新元素数量
        initial_count = len(driver.find_elements(By.CSS_SELECTOR, ".movie-list-item.playable.unwatched"))

    print("All content loaded.")
    driver.execute_script("window.scrollTo(0, 0);")

def tranInfodist(infos):
    infos_dist = {}
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


def get_info(driver):
    movie_info = {}
    infos = driver.find_element(By.CSS_SELECTOR, "#info").text.split("\n")
    infos_dist = tranInfodist(infos)
    if "主演" in infos_dist:
        movie_info["主演"] = "".join([driver.execute_script("return arguments[0].textContent", type) for type in
                                      driver.find_elements(By.CSS_SELECTOR,
                                                           "#info > span:nth-child(5) > span.attrs > * ")[
                                      :-1]])
    movie_info["电影"] = driver.find_element(By.CSS_SELECTOR, "#content > h1 > span").text
    movie_info["海报"] = driver.find_element(By.CSS_SELECTOR, "#mainpic > a > img").get_attribute('src').split('/')[-1]
    movie_info["导演"] = infos_dist.get("导演", "")
    movie_info["编剧"] = infos_dist.get("编剧", "")
    movie_info["主演"] = infos_dist.get("主演", "")
    movie_info["类型"] = "/".join([type.text for type in driver.find_elements(By.CSS_SELECTOR, "[property='v:genre']")])
    movie_info["制片国家/地区"] = infos_dist.get("制片国家/地区", "")
    movie_info["语言"] = infos_dist.get("语言", "")
    movie_info["上映日期"] = infos_dist.get("上映日期", "")
    movie_info["片长"] = infos_dist.get("片长", "")
    movie_info["又名"] = infos_dist.get("又名", "")
    movie_info["IMDb"] = infos_dist.get("IMDb", "")
    movie_info["评分"] = driver.find_element(By.CSS_SELECTOR, "[property='v:average']").text
    movie_info["评价人数"] = driver.find_element(By.CSS_SELECTOR, "[property='v:votes']").text
    movie_info["简介"] = driver.find_element(By.CSS_SELECTOR, "[property='v:summary']").text
    movie_info["豆瓣链接"] = driver.current_url
    collection.insert_one(movie_info)


def get_movie_info(driver, movie_url):
    main_window_handle = driver.current_window_handle
    for url in movie_url:
        expected_url = url.get_attribute('href')
        print(expected_url)
        url.click()
        try:
            # 切换到新打开的标签页
            driver.switch_to.window(driver.window_handles[-1])
            # 等待页面加载完成
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'content')))
            # 检查URL是否被重定向
            current_url = driver.current_url
            if current_url != expected_url:
                print(f"Page redirected to {current_url}.")
                driver.close()
                driver.switch_to.window(main_window_handle)
                continue
        except TimeoutException:
            print("Page loading timed out.")
        # 获取电影信息
        get_info(driver)
        # 关闭新打开的标签页
        driver.close()
        # 切换回主标签页
        driver.switch_to.window(main_window_handle)


def get_movie_url(driver, movie_type):
    for type in movie_type:
        print(type.get_attribute('href'))
        type.click()
        time.sleep(2)
        # scrolled_to_bottom(driver)

        movie_url = driver.find_elements(By.CSS_SELECTOR,
                                         "#content > div > div.article > div.movie-list-panel.pictext > * > div > div > div.movie-name > span.movie-name-text > a")
        get_movie_info(driver, movie_url)
        driver.back()


def find_slider_gap(background_path, block_path):
    # 使用OpenCV加载图片
    background = cv2.imread(background_path, 0)
    block = cv2.imread(block_path, 0)

    # 使用OpenCV模板匹配找到滑块在背景中的位置
    result = cv2.matchTemplate(background, block, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 返回滑块的位置信息
    return max_loc[0]


def login(driver):
    login_url = driver.find_element(By.CLASS_NAME, "nav-login")
    login_url.click()
    # 短信验证
    phone_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@type='phone']")))
    phone_input.send_keys("15926159067")

    # 获取验证码
    get_captcha_button = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "account-form-field-code")))
    get_captcha_button.click()

    # 等待验证码图片加载完成
    frame = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tcaptcha_iframe_dy")))
    driver.switch_to.frame(frame)
    while True:
        try:
            img = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "slideBg")))
            # 获取元素的style属性
            style = img.get_attribute("style")
            if not style:
                time.sleep(0.5)  # 等待 0.5 秒后重试
                style = img.get_attribute("style")

            # 从style属性中提取背景图片的URL
            img_url = style.split('url("')[1].split('")')[0]
            # 下载验证码图片
            img_data = requests.get(img_url).content
            with open("captcha.jpg", "wb") as f:
                f.write(img_data)

            # 计算滑块的位置
            x, _ = get_slider_captcha_contour("captcha.jpg")
            slider = driver.find_element(By.CLASS_NAME, "tc-slider-normal")
            ActionChains(driver).drag_and_drop_by_offset(slider, x / 2 - 30, 0).perform()


            # 等待验证结果
            time.sleep(5)
            success_text = driver.find_element(By.ID, "statusSuccess").text
            if success_text:
                print("登录成功")
                break
            else:
                time.sleep(5)
                img_refresh = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#reload > img")))
                img_refresh.click()
        except Exception as e:
            print(e)

    driver.switch_to.default_content()
    captcha_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "code")))
    captcha = input("请输入验证码：")
    captcha_input.send_keys(captcha)
    # 点击登录按钮
    login_button = driver.find_element(By.CSS_SELECTOR,
                                       "#account > div.login-wrap > div.login-right > div > div.account-tabcon-start > div.account-form > div.account-form-field-submit > a")
    login_button.click()

    cookies = driver.get_cookies()
    cookie = ''.join([f"{cookie['name']}={cookie['value']};" for cookie in cookies])
    print(cookie)

    driver.back()
    return cookie
    # # 关闭新打开的标签页
    # driver.close()
    # # 切换回主标签页
    # driver.switch_to.window(driver.window_handles[0])


def main():
    url = "https://movie.douban.com/chart"

    # 配置Chrome选项
    options = Options()
    # options.add_argument('--disable-extensions')  # 禁用扩展
    # options.add_argument('--disable-gpu')  # 禁用GPU
    # options.add_argument('--no-sandbox')  # 禁用沙盒模式
    # options.add_argument('--headless')  # 如果需要无头浏览器

    # 添加请求头
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')

    # 配置代理
    # options.add_argument('--proxy-server=http://' + proxy)

    # 启动Chrome浏览器
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(url)
    # login(driver)
    movie_type = driver.find_elements(By.CSS_SELECTOR, "a[href^='/typerank?type_name=']")
    get_movie_url(driver, movie_type)
    input('等待回车键结束程序')



if __name__ == '__main__':
    main()
