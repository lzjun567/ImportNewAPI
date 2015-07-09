#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

import os

import tornado
import tornado.template
from tornado.options import define, options

path = lambda root, *a: os.path.join(root, *a)
ROOT = os.path.dirname(os.path.abspath(__file__))

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="debug mode")
tornado.options.parse_command_line()

MEDIA_ROOT = path(ROOT, 'static')
TEMPLATE_ROOT = path(ROOT, 'templates')
settings = dict({"login_url": "/login"})
settings['debug'] = options.debug
settings['static_path'] = MEDIA_ROOT
settings['template_loader'] = tornado.template.Loader(TEMPLATE_ROOT)

tornado.options.parse_config_file("config.py")

if __name__ == '__main__':
    pass
