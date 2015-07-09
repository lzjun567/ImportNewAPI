#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

from handlers import *

url_patterns = [
    (r"/items", ItemListHandler),
    (r"/items/(\d+)", ItemDetailHandler)

]
