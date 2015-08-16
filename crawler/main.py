#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

import os
import sys
import logging
import time
from datetime import timedelta

from tornado import queues
from tornado import gen
from tornado import ioloop

from core import crawl_detail_info, crawl_base_info

PROJECT_PATH = os.path.realpath(os.path.join("..", os.path.dirname(__file__)))
if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)

from models import JavaPost, PythonPost
import config

base_concurrency_num = 10
detail_concurrency_num = 50


@gen.coroutine
def main(category, page_count):
    start = time.time()
    base_info_queue = queues.Queue()  # 解析基本信息的队列
    detail_info_queue = queues.Queue()  # 解析正文内容的队列
    url = config.java_source if category == 'java' else config.python_source
    for page in range(1, page_count + 1):
        url = url if page == 1 else url + "/page/%d" % page
        base_info_queue.put(url)

    @gen.coroutine
    def base_info_work():
        """
        解析基本的信息的进程
        :return:
        """
        while True:
            current_url = yield base_info_queue.get()
            posts = yield crawl_base_info(current_url)
            for post in posts:
                yield detail_info_queue.put(post)
            base_info_queue.task_done()

    @gen.coroutine
    def detail_info_work():
        while True:
            raw_post = yield detail_info_queue.get()
            post = yield crawl_detail_info(raw_post)
            obj = JavaPost(**post) if category == 'java' else PythonPost(**post)
            obj.save()
            detail_info_queue.task_done()

    for _ in range(base_concurrency_num):
        # 启动concurrency_num数量的进程
        base_info_work()

    for _ in range(detail_concurrency_num):
        detail_info_work()

    yield base_info_queue.join(timeout=timedelta(seconds=300))
    yield detail_info_queue.join(timeout=timedelta(seconds=300))
    print('Done in %d seconds' % (time.time() - start))


if __name__ == '__main__':
    logging.basicConfig()
    io_loop = ioloop.IOLoop.current()
    category, page_count = 'python', 1
    io_loop.run_sync(lambda: main(category, page_count))
