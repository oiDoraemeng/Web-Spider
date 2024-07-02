import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import time


from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

from function import get_slider_captcha_contour

def login(PHONE):
    url = "https://movie.douban.com/chart"

    # 配置Chrome选项
    options = Options()
    # 添加请求头
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')

    # 启动Chrome浏览器
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(url)

    login_url = driver.find_element(By.CLASS_NAME, "nav-login")
    login_url.click()
    # 短信验证
    phone_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@type='phone']")))
    phone_input.send_keys(PHONE)

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

    driver.quit()
    return cookie