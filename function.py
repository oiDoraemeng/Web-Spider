import cv2
import numpy as np

def get_slider_captcha_contour(image_path):
    # 加载图像
    image =cv2.imread(image_path)
    # 转换图像为灰度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 使用Canny边缘检测找到图像的边缘
    edges =cv2.Canny(gray, 50, 150)
    # 使用findContours找到图像中的轮廓
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 找到轮廓的面积最大的轮廓
    max_contour = max(contours, key=cv2.contourArea)
    # 返回轮廓的坐标
    x, y, w, h = cv2.boundingRect(max_contour)
    cv2.drawContours(image, [max_contour], -1, (0, 255, 0), 2)
    # 保存带有红线框住的图像
    output_image_path = "output image .jpg"
    cv2.imwrite(output_image_path, image)

    return x, output_image_path

# 调用函数
# x, output_image_path = get_slider_captcha_contour("captcha.jpg")
# print(x)
# print(output_image_path)
