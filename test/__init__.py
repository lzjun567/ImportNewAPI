#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'liuzhijun'

from qiniu import Auth

accessKeyaccess_key = "5cBxinktzyscACMOJ_12oZt5HL0Tw6JyKeLcIHZb"
secret_key = "UEkKWa02jAViPijy0xRQULapetConVH89u0IJayV"
#coding=utf-8
__author__ = 'jemy'
'''
本例演示了一个简单的文件上传。

这个例子里面，sdk根据文件的大小选择是Form方式上传还是分片上传。
'''
import qiniu

accessKey = "5cBxinktzyscACMOJ_12oZt5HL0Tw6JyKeLcIHZb"
secretKey = "UEkKWa02jAViPijy0xRQULapetConVH89u0IJayV"

#解析结果
def parseRet(retData, respInfo):
    if retData != None:
        print("Upload file success!")
        print("Hash: " + retData["hash"])
        print("Key: " + retData["key"])

        #检查扩展参数
        for k, v in retData.items():
            if k[:2] == "x:":
                print(k + ":" + v)

        #检查其他参数
        for k, v in retData.items():
            if k[:2] == "x:" or k == "hash" or k == "key":
                continue
            else:
                print(k + ":" + str(v))
    else:
        print("Upload file failed!")
        print("Error: " + respInfo.text_body)

#无key上传，http请求中不指定key参数
def upload_without_key(bucket, filePath):
    #生成上传凭证
    auth = qiniu.Auth(accessKey, secretKey)
    upToken = auth.upload_token(bucket, key=None)

    #上传文件
    retData, respInfo = qiniu.put_file(upToken, None, filePath)

    #解析结果
    parseRet(retData, respInfo)


def main():
    bucket = "blog-resource"
    filePath = "/Users/lzjun/C2E5BC888C71ECBB57170F3D74BED8F5.png"
    upload_without_key(bucket, filePath)


if __name__ == "__main__":
    main()