#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

from datetime import datetime
from datetime import timedelta
import os
import sys
import traceback
import time
import logging

from bs4 import BeautifulSoup
from bs4 import Comment
from tornado import gen
from tornado import queues
from tornado import httpclient
from tornado import ioloop
from tornado.httpclient import HTTPError

PROJECT_PATH = os.path.realpath(os.path.join("..", os.path.dirname(__file__)))
if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)

from models import Post

BASE_URL = "http://www.importnew.com/all-posts"
base_concurrency_num = 10
detail_concurrency_num = 50
MAX_PAGE = 46  # 根据实际情况来决定你要解析多少页


@gen.coroutine
def crawl_base_info(url):
    """
    从文章列表页面爬基本信息：title， description，cover, create_at
    :param url :http://www.importnew.com/all-posts
    :return: 返回文章列表集合
    """
    response = yield httpclient.AsyncHTTPClient().fetch(url)
    soup = BeautifulSoup(response.body)
    archives = soup.find_all('div', class_="post floated-thumb")
    results = list()
    for index, archive in enumerate(archives):
        try:
            post_thumb = archive.find('div', class_="post-thumb")
            cover = post_thumb.a.img['src'] if post_thumb else ""
            meta = archive.find("div", class_="post-meta")
            url = meta.p.a['href']
            title = meta.find(class_="meta-title").string
            description = meta.find('span', class_="excerpt").p.string or ""
            create_at = meta.p.contents[2].replace("|", '').strip()
            # 抓取时间时同一天发布的文章只能取得到年月日，手动加上时分秒，先解析文章当作最新发布的
            create_at = datetime.strptime(create_at, "%Y/%m/%d") - timedelta(minutes=index)
            params = {"title": title, 'url': url, 'description': description, 'cover': cover,
                      'create_at': create_at, }
            post = Post(**params)
            results.append(post)
        except:
            print traceback.format_exc()
    raise gen.Return(results)


@gen.coroutine
def crawl_detail_info(post):
    """
    爬文章详情：author, content
    :param post:
    :return:
    """
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(post.url, request_timeout=5)
        detail_soup = BeautifulSoup(response.body)
    except HTTPError:
        print traceback.format_exc()
        raise gen.Return()

    def get_author(soup):
        """
        获取作者信息
        """
        copyright_area = soup.find(class_="copyright-area")
        a_tags = copyright_area.find_all("a")
        if a_tags and len(a_tags) == 1:
            author_name = a_tags[0].text
        elif a_tags and len(a_tags) > 1:
            author_name = a_tags[1].text
        else:
            author_name = ""
        return author_name

    def get_body(soup):
        """
        获取文章正文
        """
        body = soup.find(class_="entry")
        # 去掉头部版权信息和文末的作者信息和注释
        body.find(class_="copyright-area").extract()
        author_bio = body.find(id="author-bio")
        author_bio.extract() if author_bio else None
        comments = body.findAll(text=lambda text: isinstance(text, Comment))
        map(lambda x: x.extract(), comments)

        html = BeautifulSoup(u"""
        <body class="single single-post single-format-standard chrome">
        <div class="container" id="wrapper">
        <div class="grid-8">
        <div class="post type-post status-publish format-standard hentry category-basic tag-47 odd">
        """)
        title = BeautifulSoup(u"""
            <div class="entry-header">
            <h1 style="margin-top:10px">{title}</h1>
            </div>""".format(title=post.title))
        html.find(class_='post').append(title)
        html.find(class_="post").append(body)
        return str(html)

    author = get_author(detail_soup)
    content = get_body(detail_soup)
    post.author = author
    post.content = content
    post.save()


@gen.coroutine
def main():
    start = time.time()
    base_info_queue = queues.Queue()  # 解析基本信息的队列
    detail_info_queue = queues.Queue()  # 解析正文内容的队列

    for page in range(1, MAX_PAGE):
        url = BASE_URL if page == 1 else BASE_URL + "/page/%d" % page
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
            post = yield detail_info_queue.get()
            yield crawl_detail_info(post)
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
    io_loop.run_sync(main)
