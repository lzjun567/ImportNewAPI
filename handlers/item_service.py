#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

import tornado

from base import BaseHandler
from models import Post


class ItemListHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        try:
            first_id = int(self.get_argument("f_id", None))
        except TypeError:
            first_id = None
        last_id = int(self.get_argument("l", 0))
        count = int(self.get_argument("c", 20))
        if first_id is not None:
            items = Post.find_many_by_time_over_id(first_id, 0, count)
        else:
            items = Post.find_many(start=last_id, num=count)
        self.write({"posts": items, 'l': last_id + len(items)})


class ItemDetailHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self, item_id):
        post = Post.find_one(item_id)
        self.write({"post": post})
