#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'
import time
from datetime import datetime

import redis

import config

conn = redis.StrictRedis(host=config.redis_host, port=config.redis_port, db=config.redis_db)


class Post(object):
    # redis key
    KEY_POST_IDS = "posts"  # 帖子列表 sorted set
    KEY_POST_DETAIL = "post:{id}"  # 帖子详情 hash
    KEY_URL_ID = "url:id"  # url与id的映射 hash

    def __init__(self, **kwargs):
        self.id = None
        self.url = ""
        self.title = ""
        self.description = ""
        self.content = ""
        self.cover = ""  # 封面
        self.create_at = None
        self.author = ""

        self.__dict__.update(kwargs)

    def __repr__(self):
        return "id:%s title:%s " % (self.id, self.title)

    def save(self):
        score = time.mktime(self.create_at.timetuple())
        self.id = conn.hget(self.KEY_URL_ID, self.url)
        if not self.id:
            self.id = self._auto_increment()
            conn.hset(self.KEY_URL_ID, self.url, self.id)
            conn.zadd(self.KEY_POST_IDS, score, self.id)
        else:
            # 该文章存在时，创建时间不再更新，只更新其他字段
            del self.create_at
        key = self.KEY_POST_DETAIL.format(id=self.id)
        values = vars(self)
        conn.hmset(key, values)
        return self

    @classmethod
    def find_one(cls, item_id):
        item = conn.hgetall(cls.KEY_POST_DETAIL.format(id=item_id))
        if item:
            return Post(**item)

    @classmethod
    def find_many_by_time_over_id(cls, item_id, start=0, num=10):
        """
        基于item_id返回发布时间大于该帖子的列表
        :return:
        """
        post = cls.find_one(item_id)
        if post:
            score = time.mktime(datetime.strptime(post.create_at, "%Y-%m-%d %H:%M:%S").timetuple())
            ids = conn.zrevrangebyscore(cls.KEY_POST_IDS, "+inf", "(%s" % score, start=start, num=num)
        else:
            ids = []
        return cls.find_many_by_ids(ids)

    @classmethod
    def find_many(cls, category='python', start=0, num=10):
        """
        获取多条
        :param start: 起始位置
        :param num: 返回的数量
        :return:
        """
        key = cls.KEY_POST_DETAIL
        ids = conn.zrevrange(cls.KEY_POST_IDS, start, end=start + num - 1)
        return cls.find_many_by_ids(ids)

    @classmethod
    def find_many_by_ids(cls, ids):
        if isinstance(ids, basestring):
            ids = [ids]
        items = []
        for _id in ids:
            item = conn.hgetall(cls.KEY_POST_DETAIL.format(id=_id))
            if item:
                item.pop("content", None)
                items.append(Post(**item))
        return items;

    @staticmethod
    def _auto_increment():
        return conn.incr('next_id')


class PythonPost(Post):
    # redis key
    KEY_POST_IDS = "python-posts"  # 帖子列表 sorted set


class JavaPost(Post):
    # redis key
    KEY_POST_IDS = "java-posts"  # 帖子列表 sorted set


if __name__ == '__main__':
    print Post.find_many_by_time_over_id(6)
