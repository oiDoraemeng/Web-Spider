import os
import yaml


def read_config():
    # 获取yaml文件路径
    yamlPath = os.path.join(os.getcwd(), "Config.yaml")

    # open方法打开直接读出来
    f = open(yamlPath, 'r', encoding='utf-8')
    cfg = f.read()
    return yaml.safe_load(cfg)  # 用load方法转字典


CONFIG = read_config()
