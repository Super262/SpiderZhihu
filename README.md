# SpiderZhihu
A crawler for Zhihu (https://www.zhihu.com).

## 一、 目标网站分析

### 1. 网站名称
知乎（https://www.zhihu.com）

### 2. 数据记录的结构

```
使用Elasticsearch统一存储知乎上“问题”的标题和内容

字段名, 类型
suggest, Completion
question_id, Keyword
title, Text
content, Keyword
answer_num, Integer
source, Keyword
url, Keyword
```

## 二、 所使用的开发工具

### 1. 开发语言

Python 3
### 2. 其它模块
```
Scrapy 2.1.0（爬取网站数据、提取结构性数据的应用程序框架）
selenium 3.141.0（一个用于Web应用程序测试的工具）
mouse 0.7.1（模拟鼠标点击）
requests 2.22.0（处理网络请求）
peewee 3.13.3（访问MySQL）
elasticsearch-dsl 5.1.0（访问Elasticsearch）
zheye （倒立汉字识别，https://github.com/996refuse/zheye）
```
