#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

import tornado.web

import tornado.ioloop

from urls import url_patterns
from settings import settings


class ImportNewApp(tornado.web.Application):
    def __init__(self):
        tornado.web.Application.__init__(self, handlers=url_patterns, **settings)
