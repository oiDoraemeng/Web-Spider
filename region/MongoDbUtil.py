#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib
from collections import Mapping
from typing import Any

import pymongo
from pymongo import MongoClient
from pymongo.database import Database


class MongoDbUtil(object):
    """
    MongoDb工具类
        这个类提供了针对MongoDB的连接，
        基础的增删改查方法等常用工具
    """

    def __init__(self, config):
        """
        工具类初始化
        :param config:一个字典，里面应包含database,user,pwd,host,port
        """
        self._database = config.get("database")  # 数据库名
        self._username = config.get("username")  # 用户名
        self._password = config.get("password")  # 密码
        self._host = config.get("host")  # 数据库地址
        self._port = config.get("port")  # 端口号
        self._connect = None  # 数据库连接
        self.db: Database[Mapping[str, Any]] = None  # 数据库集合
        if not self._is_available():
            self._get_connect()

    def _is_available(self):
        """
        判断连接是否可用
        :return:bool
        """
        return self._connect is not None and self.db is not None

    def _get_connect(self):
        """
        获取数据库连接
        :return:
        """
        # 连接不可用,则打开新的连接
        if not self._is_available():
            try:
                if len(self._username):
                    # 有密码登录
                    clientStr = "mongodb://{}:{}@{}:{}/{}".format(
                        self._username,
                        urllib.parse.quote_plus(self._password),
                        self._host,
                        self._port,
                        self._database)
                    self._connect = MongoClient(clientStr)
                    self.db = self._connect.get_database(self._database)
                else:
                    # 无密码登录
                    self._connect = MongoClient(host=self._host, port=self._port)
                    self.db = self._connect.get_database(self._database)
            except Exception as e:
                raise Exception('打开连接失败,{}', format(e))

    def insert_one(self, collection, data):
        """
        在集合中插入单条数据
        :param collection: 集合名
        :param data: 要插入的数据
        :return:objectId 插入数据后的objectId
        """
        if collection is None or collection == "":
            return False
        try:
            if not self._is_available():
                self._get_connect()
            result = self.db[collection].insert_one(data)
            return result.inserted_id
        except Exception as e:
            raise Exception('Mongo insert_one error:{}', format(e))

    def insert_many(self, collection, data):
        """
        在集合中插入多条数据
        :param collection:集合名
        :param data:要插入的数据
        :return:int 插入成功的条数
        """
        if collection is None or collection == "":
            return False
        try:
            if not self._is_available():
                self._get_connect()
            result = self.db[collection].insert_many(data, ordered=False)
            return len(result.inserted_ids)
        except Exception as e:
            raise Exception("Mongo insert_many error:{}".format(e))

    def update_batch(self, collection, condition, data, model=False):
        """
        批量修改集合
        :param collection:集合名
        :param condition:匹配条件
        :param data:要修改的数据
        :param model:是否使用upsert模式
        :return:修改成功的条数
        """
        try:
            if not self._is_available():
                self._get_connect()
            result = self.db[collection].update_many(condition, {"$set": data}, upsert=model)
            return result.modified_count
        except Exception as e:
            raise Exception("Mongo updateBatch error:{} collection:{} || data:{}".format(e, collection, data))

    def update_one(self, collection, condition, data, model=False):
        """
        修改一条集合中的数据
        :param collection:集合名
        :param condition:匹配条件
        :param data:数据
        :param model:是否使用upsert模式
        :return:int 修改成功的条数
        """
        try:
            if not self._is_available():
                self._get_connect()
            result = self.db[collection].update_one(condition, {'$set': data}, upsert=model)
            return result.modified_count
        except Exception as e:
            raise Exception("Mongo updateOne error:{} collection:{} || data:{}".format(e, collection, data))

    def update_many(self, collection, condition, data, model=False):
        """
        批量修改数据
        :param collection:集合名
        :param condition:条件
        :param data:数据
        :param model:是否使用upsert模式
        :return:int 修改成功的条数
        """
        try:
            if not self._is_available():
                self._get_connect()
            bulkList = []
            for d in data:
                cond = {}
                for key in condition:
                    cond[key] = d[key]
                bulkList.append(pymongo.UpdateOne(cond, {'$set': d}, upsert=model))
            result = self.db[collection].bulk_write(bulkList, ordered=False)
            return result.upserted_count
        except Exception as e:
            raise Exception("Mongo updateOne error:{} collection:{} || data:{}".format(e, collection, data))

    def find(self, collection, condition, column=None):
        """
        条件查询
        :param collection: 集合名
        :param condition:查询条件,字典
        :param column: 需要显示的列,默认全部显示
        :return:一个包含查询结果的列表
        """
        try:
            if not self._is_available():
                self._get_connect()
            return self.db[collection].find(condition, column)
        except Exception as e:
            raise Exception("Mongo find error:{}".format(e))

    def aggregate(self, collection, condition):
        """
        集算器
        :param collection:集合名
        :param condition:集算条件
        :return:结果集的游标
        """
        try:
            if not self._is_available():
                self._get_connect()
            return self.db[collection].aggregate(condition)
        except Exception as e:
            raise Exception("Mongo aggregate error:{}".format(e))

    def find_one(self, collection, condition, column=None):
        """
        根据条件查询第一条匹配的数据
        :param collection:集合名
        :param condition:条件
        :param column:需要显示的列
        :return:包含结果的字典
        """
        try:
            if not self._is_available():
                self._get_connect()
            return self.db[collection].find_one(condition, column)
        except Exception as e:
            raise Exception("Mongo findOne error:{}".format(e))

    def counts(self, collection, condition=None):
        """
        获取符合条件的记录的数量
        :param collection:集合名
        :param condition:匹配条件
        :return:number 匹配到的数量
        """
        try:
            if not self._is_available():
                self._get_connect()
            if condition is None or condition == "":
                condition = {"_id": {"$ne": "null"}}
            return self.db[collection].count_documents(condition)
        except Exception as e:
            raise Exception("Mongo counts except error:{}".format(e))

    def aggregate_counts(self, collection, condition):
        """
        使用集算器获取符合条件的数量(未优化)
        :param collection:集合名
        :param condition:查询条件
        :return:符合条件的记录的数量
        """
        try:
            if not self._is_available():
                self._get_connect()
            condition.append({'$count': 'count'})
            data = list(self.db[collection].aggregate(condition))
            if len(data) > 0:
                return data[0]['count']
            return 0
        except Exception as e:
            raise Exception("Mongo aggregateCounts error:{}".format(e))

    def delete(self, collection, condition):
        """
        根据条件删除数据
        :param collection:集合名
        :param condition:匹配条件
        :return:操作成功的数量
        """
        try:
            if not self._is_available():
                self._get_connect()
            return self.db[collection].delete_many(filter=condition).deleted_count
        except Exception as e:
            raise Exception("Mongo delete error:{}".format(e))
