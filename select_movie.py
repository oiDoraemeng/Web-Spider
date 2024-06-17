import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pymongo import MongoClient

# 连接MongoDB数据库
client = MongoClient('mongodb://192.168.1.10:27017/')

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

    # 获取页面总高度
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # 模拟滚动到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 等待加载更多内容
        time.sleep(1)  # 根据实际情况调整等待时间

        # 计算新的页面高度
        new_height = driver.execute_script("return document.body.scrollHeight")

        # 检查是否已滚动到底部
        if new_height == last_height:
            break
        last_height = new_height


def tranInfodist(infos):
    infos_dist = {}
    for info in infos:
        try:
            # if "：" in info:  # 处理中文冒号
            #     key, value = info.split("：",1)
            # else:  # 处理英文冒：
            key, value = info.split(":",1)
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
                                  driver.find_elements(By.CSS_SELECTOR, "#info > span:nth-child(5) > span.attrs > * ")[
                                  :-1]])
    movie_info["电影"] = driver.find_element(By.CSS_SELECTOR, "#content > h1 > span").text
    movie_info["海报"] = driver.find_element(By.CSS_SELECTOR, "#mainpic > a > img").get_attribute('src').split('/')[-1]
    movie_info["导演"] = infos_dist.get("导演", "")
    movie_info["编剧"] = infos_dist.get("编剧", "")
    movie_info["主演"] = infos_dist.get("主演", "")
    movie_info["类型"] = "/".join([type.text for type in driver.find_elements(By.CSS_SELECTOR, "[property='v:genre']")])
    movie_info["制片国家/地区"] = infos_dist.get("制片国家/地区","")
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

def login(driver):
    login_url = driver.find_element(By.CLASS_NAME, "nav-login")
    login_url.click()
    try:
        # 等待页面加载完成
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "account-tab-account")))
        password_login = driver.find_element(By.CLASS_NAME,"account-tab-account")
        password_login.click()
        # 输入用户名密码
        username = driver.find_element(By.ID, "username")
        password = driver.find_element(By.ID, "password")
        username.send_keys("15926159067")
        password.send_keys("123456789cr")
        # 点击登录按钮
        login_button = driver.find_element(By.CSS_SELECTOR, "#account > div.login-wrap > div.login-right > div > div.account-tabcon-start > div.account-form > div.account-form-field-submit > a")
        login_button.click()
        # 等待页面加载完成
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "nav-login")))
        # 关闭新打开的标签页
        driver.close()
        # 切换回主标签页
        driver.switch_to.window(driver.window_handles[0])
    except TimeoutException:
        print("Page loading timed out.")

def main():
    url = "https://movie.douban.com/chart"

    # 配置Chrome选项
    # options = Options()
    # options.add_argument('--disable-extensions')  # 禁用扩展
    # options.add_argument('--disable-gpu')  # 禁用GPU
    # options.add_argument('--no-sandbox')  # 禁用沙盒模式
    # options.add_argument('--headless')  # 如果需要无头浏览器
    # 启动Chrome浏览器
    driver = webdriver.Chrome()
    driver.get(url)
    login(driver)
    movie_type = driver.find_elements(By.CSS_SELECTOR, "a[href^='/typerank?type_name=']")
    get_movie_url(driver, movie_type)
    input('等待回车键结束程序')


if __name__ == '__main__':
    main()
