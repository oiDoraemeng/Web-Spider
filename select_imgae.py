import os
import time

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

# 指定下载路径
download_path = r"./images"

# 确保下载路径存在
if not os.path.exists(download_path):
    os.makedirs(download_path)

# 模拟滚动加载图片
def lazy_load_img(driver):
    # 获取页面总高度
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # 向下滚动一段距离
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(0.5)  # 等待0.5秒加载内容

        # 计算新的滚动高度并与最后的滚动高度进行比较
        new_height = driver.execute_script("return window.scrollY;")
        if new_height == last_height:
            break
        last_height = new_height

def download_img(img_src):
    for src in img_src:

        src = src.get_attribute("src")
        print(src)
        response = requests.get(src)

        # 从URL中获取图片文件名
        file_name = src.split("/")[-5][:8]

        # 保存图片
        with open(os.path.join(download_path, file_name + ".jpg"), "wb") as f:
            f.write(response.content)
def main():

    url = 'https://www.bizhi99.com/zuixin'

    # 启动Chrome浏览器
    driver = webdriver.Chrome()
    driver.get(url)

    while True:
        lazy_load_img(driver)
        img_src=(driver.find_elements(By.CSS_SELECTOR, "img.lazy"))
        # 找到下一页按钮
        try:
            next_page = driver.find_element(By.LINK_TEXT, "下一页")
        except NoSuchElementException:# 没有下一页按钮
            next_page = None
        if next_page is None:
            break
        print(next_page.get_attribute("href"))
        download_img(img_src)
        next_page.click()


    input('等待回车键结束程序')
if __name__ == '__main__':
    main()
