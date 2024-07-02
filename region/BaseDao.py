import copy
import uuid
import hashlib
from bson import ObjectId

from Config import CONFIG
from LogUtil import Logger
from MongoDbUtil import MongoDbUtil

logger = Logger(CONFIG.get('log'))

conn = MongoDbUtil(CONFIG.get('mongodb'))


class BaseDao:
    def __init__(self, collection, primaryKey):
        self.collection = collection  # 数据库集合名
        self.primaryKey = primaryKey  # 当前集合的主键字段
        self.conn: MongoDbUtil = None  # 数据库连接
        self._getConn()
        self.id = self.getId()

    def _getConn(self):
        """
        # 获取MongoDB数据库连接
        :return: 数据库连接
        """
        if self.conn is None:
            try:
                # self.conn = MongoDbUtil(CONFIG.get('mongodb'))
                self.conn = conn
            except Exception as e:
                logger.error('实例化MongoDbs失败,{}'.format(e))

    def getDB(self):
        """
        获取MongoDB原始数据库指针
        :return:
        """
        return self.conn.db[self.collection]

    def save(self, data):
        """
        向集合中添加一条数据
        :param data:待添加的数据
        :return:添加的_id值
        """
        try:
            _id = self.conn.insert_one(self.collection, data)
            return _id
        except Exception as e:
            logger.error("插入单条数据失败,{}".format(e))
            return None

    def saveMany(self, data):
        """
        向集合中添加一条数据
        :param data:待添加的数据
        :return:添加成功的数量
        """
        try:
            ret = self.conn.insert_many(self.collection, data)
            return ret
        except Exception as e:
            # logger.error("插入多条数据失败{}".format(e))
            return -1

    def deleteByKey(self, key):
        """
        根据默认主键删除数据
        :param key: 要删除数据的主键的值
        :return:删除的条数
        """
        try:
            ret = self.conn.delete(self.collection, {self.primaryKey: key})
            return ret
        except Exception as e:
            logger.error("根据主键删除数据失败{}".format(e))
            return -1

    def batchRemove(self, keys):
        """
        根据主键批量删除
        :param keys:主键列表
        :return:删除的条数
        """
        try:
            ret = self.conn.delete(self.collection, {self.primaryKey: {'$in': keys}})
            return ret
        except Exception as e:
            logger.error("批量删除数据失败,{}".format(e))
            return -1

    def deleteByCondition(self, condition):
        """
        根据条件删除数据
        :param condition: 条件
        :return: 成功删除的的条数
        """
        try:
            ret = self.conn.delete(self.collection, condition)
            return ret
        except Exception as e:
            logger.error("根据条件删除数据失败,{}".format(e))
            return -1

    def updateByKey(self, key, data, upsert=False):
        """
        根据默认主键更新数据
        :param key: 主键的值
        :param data: 数据
        :param upsert: 不存在则插入
        :return:更新的数量
        """
        try:
            state = self.conn.update_one(self.collection, {self.primaryKey: key}, data, upsert)
            return state
        except Exception as e:
            logger.error("根据主键更新数据失败{}".format(e))
            return -1

    def updateByCondition(self, condition, data, upsert=False):
        """
        根据条件更新数据
        :param condition:查询条件
        :param data:更新数据
        :param upsert: 不存在则插入
        :return:更新的状态,bool
        """
        try:
            state = self.conn.update_batch(self.collection, condition, data, upsert)
            return state
        except Exception as e:
            logger.error("批量更新数据失败{}".format(e))
            return -1

    def updateMany(self,condition, data, upsert=False):
        try:
            state = self.conn.update_many(self.collection,condition, data, upsert)
            return state
        except Exception as e:
            logger.error("批量更新数据失败{}".format(e))
            return -1

    def selectByKey(self, key, column=None):
        """
        根据默认主键获取数据
        :param column:
        :param key:主键的值
        :return:查询到的数据,默认为None
        """
        data = self.conn.find_one(self.collection, {self.primaryKey: key}, column)
        return data

    def selectByCondition(self, condition, column=None):
        """
        根据条件获取数据
        :param column:
        :param condition: 条件
        :return: 数据,数据条数
        """

        data = list(self.conn.find(self.collection, condition, column))
        count = len(data)
        return data, count

    def page(self, condition, page=1, limit=10, sortArgs=None, colume=None):
        """
        分页查询
        :param sortArgs: 排序参数
        :param condition:查询条件
        :param page:当前页数
        :param limit:每页数据条数
        :return:数据,数据总数
        """

        total_num = self.conn.counts(self.collection, condition)
        page_total_num = total_num // limit  # 总页数
        if total_num % limit: page_total_num += 1
        # 范围限制
        if page < 1:
            page = 1
        if page_total_num == 0:
            start = 0
        elif page > page_total_num:
            start = (page_total_num - 1) * limit
        else:
            start = (page - 1) * limit
        if sortArgs is not None:
            data = list(self.conn.find(self.collection, condition, colume).limit(limit).skip(start).sort(sortArgs))
        else:
            data = list(self.conn.find(self.collection, condition, colume).limit(limit).skip(start))

        return data, total_num

    def aggregate(self, condition):
        """
        多表查询
        :param condition:查询条件
        :param page:当前页数
        :param limit:每页数据条数
        :return:数据,数据总数
        """
        data = list(self.conn.aggregate(self.collection, condition))
        return data

    def lookup(self, From, localField, foreignField, As):
        """
        集算器连表
        :param From:从表表名
        :param localField:主表字段
        :param foreignField:从表外键字段
        :param As:别名
        :return:
        """
        data = {
            '$lookup':
                {
                    'from': From,
                    'localField': localField,
                    'foreignField': foreignField,
                    'as': As
                }
        }
        return data

    def match(self, condition):
        """
        集算器筛选条件
        :param condition:匹配条件
        :return:
        """
        data = {
            '$match': condition
        }
        return data

    def sort(self, condition):
        """
        集算器筛选条件
        :param condition:匹配条件
        :return:
        """
        data = {
            '$sort': condition
        }
        return data

    def aggregatePage(self, condition, page=1, limit=10):
        """
        多表分页查询
        :param condition:查询条件
        :param page:当前页数
        :param limit:每页数据条数
        :return:数据,数据总数
        """
        total = self.conn.aggregate_counts(self.collection, copy.deepcopy(condition))
        skip = (page - 1) * limit
        condition.append({'$skip': skip})
        condition.append({'$limit': limit})
        data = list(self.conn.aggregate(self.collection, condition))
        return data, total

    def aggregateCount(self, condition):
        """
        查询数量
        :param condition:查询条件
        :return:数据,数据总数
        """
        total = self.conn.aggregate_counts(self.collection, copy.deepcopy(condition))
        return total

    def useMD5(self, text):
        md5 = hashlib.md5()
        md5.update(text.encode(encoding='utf-8'))
        return md5.hexdigest()

    def getId(self):
        return uuid.uuid1().hex

    def getKeyId(self):
        """
        获取一个可用的主键
        :return:
        """
        ret = self.conn.db['primary_key_id'].find_one_and_update({'tableName': self.collection}, {"$inc": {'id': 1}})
        new = ret['id']
        return new

    def getObjectId(self):
        return ObjectId()

    def parseParam(self, param):
        """
        解析参数
        :param param:
        :return:
        """
        paramDict = {
            'page': None,
            'other': None,
            'data': None
        }
        # 解析参数
        data = {}
        page = {}
        other = {}
        for k, v in param.items():
            if k in ['pageNum', 'pageSize']:
                page[k] = int(v)
            elif 'params[' in k:
                key = k.replace('params[', '').replace(']', '')
                other[key] = v
            else:
                data[k] = v
        if len(data) > 0:
            paramDict['data'] = data
        if len(page) > 0:
            paramDict['page'] = page
        if len(other) > 0:
            paramDict['other'] = other
        return paramDict
