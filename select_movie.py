import os
import time


from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from pymongo import MongoClient

# 连接MongoDB数据库
client = MongoClient('mongodb://localhost:27017/')

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

def get_info(driver):
    movie_info = {}
    movie_info["电影"] = driver.find_element(By.CSS_SELECTOR, "#content > h1 > span").text
    movie_info["海报"] = driver.find_element(By.CSS_SELECTOR, "#mainpic > a > img").get_attribute('src').split('/')[-1]
    movie_info["导演"] = driver.find_element(By.CSS_SELECTOR, "#info > span:nth-child(1) > span.attrs").text
    movie_info["编剧"] = driver.find_element(By.CSS_SELECTOR, "#info > span:nth-child(3) > span.attrs").text
    movie_info["主演"] = driver.find_element(By.CSS_SELECTOR, "#info > span:nth-child(5) > span.attrs > * > a").text
    movie_info["类型"] = driver.find_element(By.CSS_SELECTOR, "#info > span:nth-child(8), #info > span:nth-child(9)").text
    movie_info["制片国家/地区"] = driver.find_element(By.XPATH, "//span[contains(text(), '制片国家/地区')]").find_element(By.XPATH, "./following-sibling::text()")  # 获取相邻文本节点
    movie_info["语言"] = driver.find_element(By.XPATH, "//span[contains(text(), '语言')]").find_element(By.XPATH, "./following-sibling::text()")
    movie_info["上映日期"] = driver.find_element(By.CSS_SELECTOR, "#info > span:nth-child(16), #info > span:nth-child(17)").text
    movie_info["片长"] = driver.find_element(By.CSS_SELECTOR, "#info > span:nth-child(20)").text
    movie_info["又名"] = driver.find_element(By.XPATH, "//span[contains(text(), '又名')]").find_element(By.XPATH, "./following-sibling::text()")
    movie_info["IMDb链接"] = driver.find_element(By.XPATH, "//span[contains(text(), 'IMDb')]").find_element(By.XPATH, "./following-sibling::text()")
    movie_info["评分"] = driver.find_element(By.CSS_SELECTOR, "#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong").text
    movie_info["评价人数"] = driver.find_element(By.CSS_SELECTOR, "#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > div > div.rating_sum > a > span").text
    movie_info["简介"] = driver.find_element(By.CSS_SELECTOR, "#link-report-intra > span.short > span").text
    movie_info["豆瓣链接"] = driver.current_url
    collection.insert_one(movie_info)
def get_movie_info(driver,movie_url):
    main_window_handle = driver.current_window_handle
    for url in movie_url:
        print(url.get_attribute('href'))
        url.click()
        # 切换到新打开的标签页
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)
        get_info(driver)
        # 关闭新打开的标签页
        driver.close()
        # 切换回主标签页
        driver.switch_to.window(main_window_handle)

def get_movie_url(driver,movie_type):
    for type in movie_type:
        print(type.get_attribute('href'))
        type.click()
        time.sleep(2)
        # scrolled_to_bottom(driver)
        movie_url = driver.find_elements(By.CSS_SELECTOR, "#content > div > div.article > div.movie-list-panel.pictext > * > div > div > div.movie-name > span.movie-name-text > a")
        get_movie_info(driver,movie_url)
        driver.back()

def main():
    url ="https://movie.douban.com/chart"
    # 启动Chrome浏览器
    driver = webdriver.Chrome()
    driver.get(url)

    movie_type = driver.find_elements(By.CSS_SELECTOR, "a[href^='/typerank?type_name=']")
    get_movie_url(driver,movie_type)
    input('等待回车键结束程序')

if __name__ == '__main__':
    main()
