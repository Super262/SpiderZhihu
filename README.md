# SpiderZhihu
A crawler for Zhihu (https://www.zhihu.com).

## 一、 目标网站分析

### 1. 目标网站URL
https://www.zhihu.com

### 2. 反爬虫技术
网站主要采用验证码识别来反爬虫。用户登录时会遇到共 2 种验证码，分别是英文字母识别或倒立文字识别。如果验证码是英文字母，用户在登录前要正确识别并输入这些字母；如果验证码是倒立汉字，用户在登录前要识别并准确点击这些倒立汉字。这两种验证码在登陆界面随机出现。网站还会检查用户所使用的浏览器，屏蔽由Chrome Driver驱动的爬虫程序。

## 二、 所使用的开发工具

### 1. 开发语言
Python 3
### 2. 其它模块
```
Scrapy 2.1.0（爬取网站数据、提取结构性数据的应用程序框架）
selenium 3.141.0（一个用于Web应用程序测试的工具）
mouse 0.7.1（模拟鼠标点击）
requests 2.22.0（处理网络请求）
elasticsearch-dsl 5.1.0（访问Elasticsearch）
zheye（倒立汉字识别，https://github.com/996refuse/zheye）
```
## 三、 操作过程

### 1. 爬取目标

知乎上用户的提问

### 2. 工作思路

#### 1) 重新编译Chrome Driver
在开始爬虫之前，我重新编译了Chrome Driver。知乎会检测当前浏览网页的客户端信息，判断这个客户端是真实的浏览器，还是由Selenium驱动的爬虫程序。如果知乎检测到当前访问网页的是爬虫程序，知乎会立刻屏蔽当前访问。避开这种反爬虫策略的方式是修改Chrome Driver的源代码中某些变量的名称（如，cdc_），然后重新编译，得到没有明显特征的Chrome Driver。
```
参考 https://stackoverflow.com/questions/33225947/can-a-website-detect-when-you-are-using-selenium-with-chromedriver
```

#### 2) 识别验证码
在登录知乎时，知乎会提示输入验证码。验证码可能是倒立汉字，也可能是英文字母。这两种验证码随机出现。程序根据验证码图片的class属性来判断是哪一种验证码：若class == ‘Captcha-englishImg’，则为英文字母验证码；若class == ‘Captcha-chineseImg’，则为倒立汉字验证码。知乎登录页面的验证码的源文件使用Base64加密，加密后又填充了许多字符串（’%0A’）来防止解密。在剔除掉额外的字符串、解析经Base 64 编码的信息后，程序就可以获得验证码的原始图片（英文字母或倒立汉字）。如果验证码是英文字母，程序会请求超级鹰的API获得结果；如果验证码是倒立汉字，程序会使用zheye识别倒立文字的位置（坐标），使用mouse模块模拟鼠标点击倒立文字。
```
超级鹰：https://www.chaojiying.com
zheye：https://github.com/996refuse/zheye
```
#### 3) 获取Cookie
登录成功后，程序会获取当前的Cookie，用于之后的网络请求。
#### 4) 过滤无关域名
程序使用正则表达式（"(.*zhihu.com/question/(\d+))(/|$).*"），保留下指向“问题”页面的URL。根据获得的指向“问题”页面的URL，程序从URL末尾部分获得“问题”的ID。
#### 5) 取出“问题”
在获得“问题”详情页的文本后，程序会使用xpath选择器抽取出“问题”的标题、内容、URL、回答数量等信息。
#### 6) 数据存储
程序将获得的“问题”存储到Elasticsearch，便于分词和搜索。
### 3. 操作步骤
#### 1) 在CMD中以debug模式启动Chrome：chrome.exe --remote-debugging-port=9222；
#### 2) 启动爬虫程序后，程序首先访问登录界面；
#### 3) 识别验证码、登录成功后，程序会保存Cookie；
#### 4) 程序遍历首页的所有URL，取出符合要求的URL；
#### 5) 程序访问上步获得的URL并取出其中的“问题”；
#### 6) 程序异步地保存数据到Elasticsearch，MySQL；
#### 7) 运行时长达到设定值（如，3600 秒）后，程序自动停止；
