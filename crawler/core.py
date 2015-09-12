#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

from datetime import datetime
from datetime import timedelta
import traceback

from bs4 import BeautifulSoup, Comment
from tornado import gen
from tornado import httpclient


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
            try:
                title = meta.find(class_="archive-title").string
            except AttributeError:
                title = meta.find(class_="meta-title").string
            description = meta.find('span', class_="excerpt").p.string or ""
            try:
                create_at = meta.p.contents[2].replace("|", '').strip()
            except:
                create_at = meta.p.contents[3].replace(u'·', '').strip()
            # 抓取时间时同一天发布的文章只能取得到年月日，手动加上时分秒，先解析文章当作最新发布的
            create_at = datetime.strptime(create_at, "%Y/%m/%d") - timedelta(minutes=index)
            post = {"title": title, 'url': url, 'description': description, 'cover': cover,
                    'create_at': create_at, }
            results.append(post)
        except:
            print traceback.format_exc()
    raise gen.Return(results)


@gen.coroutine
def crawl_detail_info(post):
    """
    爬文章详情：author, content
    :param post: 字典类型，crawl_base_info返回列表中的元素
    :return:
    """
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(post.get('url'), request_timeout=5)
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
            </div>""".format(title=post.get("title")))
        html.find(class_='post').append(title)
        html.find(class_="post").append(body)
        return str(html)

    author = get_author(detail_soup)
    content = get_body(detail_soup)
    post.update({
        "author": author,
        "content": content,
    })
    raise gen.Return(post)
