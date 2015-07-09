#!/usr/bin/env python
# -*- coding: utf-8 -*-

_author__ = 'liuzhijun'

import json

import tornado.web

from models import Post


def default(obj):
    if isinstance(obj, Post):
        return obj.__dict__
    else:
        raise TypeError('%r is not JSON serializable' % obj)


class BaseHandler(tornado.web.RequestHandler):
    def write(self, chunk):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = json.dumps(chunk, default=default, separators=(',', ':'))
        super(BaseHandler, self).write(chunk)
