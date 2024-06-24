import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import time


from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from function import get_slider_captcha_contour

def login(USERNAME, PASSWORD):
    driver = webdriver.Chrome()

    driver.get("https://www.tadu.com/v3/loginpage?logintype=taduphone")

    account = driver.find_element(By.ID, "phoneAccountSwitch")
    account.click()

    wait = WebDriverWait(driver, 10)

    account_input = wait.until(EC.presence_of_element_located((By.ID, "accounts_txt")))
    account_input.send_keys(USERNAME)

    password_input = wait.until(EC.presence_of_element_located((By.ID, "password_txt")))
    password_input.send_keys(PASSWORD)

    login_btn = wait.until(EC.presence_of_element_located((By.ID, "accountLoginActive")))
    login_btn.click()

    frame = wait.until(EC.presence_of_element_located((By.ID, "tcaptcha_iframe")))
    driver.switch_to.frame(frame)

    img = wait.until(EC.presence_of_element_located((By.ID, "slideBg")))
    img_src = img.get_attribute("src")
    img_content = requests.get(img_src).content

    with open("captcha.png", "wb") as f:
        f.write(img_content)

    x,_ = get_slider_captcha_contour("captcha.png")
    print(x)

    slider = wait.until(EC.presence_of_element_located((By.ID, "tcaptcha_drag_thumb")))
    ActionChains(driver).drag_and_drop_by_offset(slider, x/2-38, 0).perform()
    slider.click()

    time.sleep(1)

    coookies = driver.get_cookies()
    cookie = ''.join([f'{cookie["name"]}={cookie["value"]}; ' for cookie in coookies])
    print(cookie)
    time.sleep(10)
    return cookie