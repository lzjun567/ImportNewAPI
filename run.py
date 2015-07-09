#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

from tornado.options import options
import tornado.ioloop
from app import ImportNewApp


def main():
    print(options.port)
    app = ImportNewApp()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
