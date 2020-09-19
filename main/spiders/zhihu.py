import re
import json
import datetime
import time
import pickle
import base64
import mouse
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from urllib import parse
from utils.zheye import zheye
from utils.ImgOCR.chaojiying import Chaojiying_Client
from scrapy.loader import ItemLoader
from main.items import ZhihuQuestionItem, ZhihuAnswerItem


class ZhihuSpider(scrapy.Spider):
    image_path = 'C:/Users/Fengwei/Documents/PycharmProjects/WebDataManagement/SpiderZhihu/file/image/yzm_cn.jpeg'
    cookie_path = 'C:/Users/Fengwei/Documents/PycharmProjects/WebDataManagement/SpiderZhihu/file/cookies/'
    driver_path = 'C:/Users/Fengwei/Documents/PycharmProjects/WebDataManagement/SpiderZhihu/chromedriver.exe'
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']
    common_url = 'https://www.zhihu.com'
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{' \
                       '0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed' \
                       '%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by' \
                       '%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count' \
                       '%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info' \
                       '%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting' \
                       '%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content' \
                       '%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B*%5D' \
                       '.topics&offset={2}&limit={1}&sort_by=default&platform=desktop '
    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 '
    }

    def parse(self, response):
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(self.common_url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果提取到question相关的页面则下载后交由提取函数进行提取
                request_url = match_obj.group(1)
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
            else:
                # 如果不是question页面则直接进一步跟踪: DFS
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
        question_id = int(match_obj.group(2))

        # 提取question的各个字段
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_css("title", "h1.QuestionHeader-title::text")
        item_loader.add_css("content", ".QuestionHeader-detail")
        item_loader.add_value("url", response.url)
        item_loader.add_value("zhihu_id", question_id)
        item_loader.add_css("answer_num", ".List-headerText span::text")
        item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
        item_loader.add_css("watch_user_num", ".NumberBoard-itemValue::text")
        item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")
        question_item = item_loader.load_item()
        # yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers,
        #                      callback=self.parse_answer)
        yield question_item

    def parse_answer(self, reponse):
        # 处理question的answer
        ans_json = json.loads(reponse.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        # chrome.exe --remote-debugging-port=9222
        chrome_options = Options()
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        browser = webdriver.Chrome(
            executable_path=self.driver_path,
            chrome_options=chrome_options)
        browser.delete_all_cookies()
        try:
            browser.maximize_window()
        except:
            pass

        browser.get('https://www.zhihu.com/signin')
        browser.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[1]/div[2]').click()
        time.sleep(3)
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[2]/div/label/input').send_keys(Keys.CONTROL + 'a')
        time.sleep(3)
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[2]/div/label/input').send_keys('17860536151')
        time.sleep(3)
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[3]/div/label/input').send_keys(Keys.CONTROL + 'a')
        time.sleep(3)
        browser.find_element_by_xpath(
            '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[3]/div/label/input').send_keys('abcdefghijk')
        time.sleep(3)
        browser.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div/div[1]/div/form/button').click()
        time.sleep(10)
        login_success = False
        while not login_success:
            browser_navigation_panel_height = browser.execute_script('return window.outerHeight - '
                                                                     'window.innerHeight;')
            try:
                notify_element = browser.find_element_by_class_name("Popover PushNotifications AppHeader-notifications")
                login_success = True
            except:
                pass

            try:
                # 尝试寻找英文验证码
                english_captcha_element = browser.find_element_by_class_name('Captcha-englishImg')
            except:
                english_captcha_element = None

            try:
                # 尝试寻找中文验证码
                chinese_captcha_element = browser.find_element_by_class_name('Captcha-chineseImg')
            except:
                chinese_captcha_element = None

            if chinese_captcha_element:
                ele_position = chinese_captcha_element.location    # 验证码的位置
                x_relative = ele_position["x"]
                y_relative = ele_position["y"]
                base64_text = chinese_captcha_element.get_attribute("src")
                code = base64_text.replace('data:image/jpg;base64,', '').replace("%0A", "")
                fh = open(self.image_path, 'wb')
                fh.write(base64.b64decode(code))    # 保存验证码图片
                fh.close()
                z = zheye()
                positions = z.Recognize(self.image_path)    # 获得倒立文字在图片上的位置

                # 计算坐标，点击倒立文字
                last_positions = []
                if len(positions) == 2:
                    if positions[0][1] > positions[1][1]:
                        last_positions.append([positions[1][1], positions[1][0]])
                        last_positions.append([positions[0][1], positions[0][0]])
                    else:
                        last_positions.append([positions[0][1], positions[0][0]])
                        last_positions.append([positions[1][1], positions[1][0]])
                    first_position = [int(last_positions[0][0] / 2), int(last_positions[0][1] / 2)]
                    second_position = [int(last_positions[1][0] / 2), int(last_positions[1][1] / 2)]
                    mouse.move(x_relative + first_position[0],
                               y_relative + browser_navigation_panel_height + first_position[1])
                    mouse.click()
                    time.sleep(3)
                    mouse.move(x_relative + second_position[0],
                               y_relative + browser_navigation_panel_height + second_position[1])
                    mouse.click()
                else:
                    last_positions.append([positions[0][1], positions[0][0]])
                    first_position = [int(last_positions[0][0] / 2), int(last_positions[0][1] / 2)]
                    mouse.move(x_relative + first_position[0],
                               y_relative + browser_navigation_panel_height + first_position[1])
                    mouse.click()

                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[2]/div/label/input').send_keys(
                    Keys.CONTROL + 'a')
                time.sleep(3)
                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[2]/div/label/input').send_keys(
                    '17860536151')
                time.sleep(3)
                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[3]/div/label/input').send_keys(
                    Keys.CONTROL + 'a')
                time.sleep(3)
                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[3]/div/label/input').send_keys(
                    'tyu223-')
                time.sleep(3)
                browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()

            if english_captcha_element:
                base64_text = english_captcha_element.get_attribute("src")
                code = base64_text.replace('data:image/jpg;base64,', '').replace("%0A", "")
                fh = open(self.image_path, 'wb')
                fh.write(base64.b64decode(code))    # 保存验证码图片
                fh.close()

                # 请求超级鹰的API
                chaojiying = Chaojiying_Client('Super262', '1234FWyueyue', '12bade4c8c081deb9765406fa5937f32')
                result = ""
                while True:
                    im = open(self.image_path, 'rb').read()
                    print("验证码坐标：")
                    json_data = chaojiying.PostPic(im, 1902)
                    print(json_data)
                    if json_data["err_no"] == 0:
                        print("识别成功！")
                        print(json_data["pic_str"])
                        result = json_data["pic_str"]    # 保存识别结果
                        break
                    else:
                        print("识别失败，继续尝试！")

                browser.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div['
                                              '4]/div/div/label/input').send_keys(Keys.CONTROL + 'a')
                time.sleep(3)
                browser.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div['
                                              '4]/div/div/label/input').send_keys(result)
                time.sleep(3)
                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[2]/div/label/input').send_keys(
                    Keys.CONTROL + 'a')
                time.sleep(3)
                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[2]/div/label/input').send_keys(
                    '17860536151')
                time.sleep(3)
                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[3]/div/label/input').send_keys(
                    Keys.CONTROL + 'a')
                time.sleep(3)
                browser.find_element_by_xpath(
                    '//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[3]/div/label/input').send_keys(
                    'tyu223-')
                time.sleep(3)
                browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()

            time.sleep(15)
            try:
                login_success = True
                Cookies = browser.get_cookies()
                print(Cookies)
                cookie_dict = {}
                for cookie in Cookies:
                    # 写入文件
                    # 此处大家修改一下自己文件的所在路径
                    f = open(self.cookie_path + cookie['name'] + '.zhihu', 'wb')
                    pickle.dump(cookie, f)
                    f.close()
                    cookie_dict[cookie['name']] = cookie['value']
                # browser.close()
                return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict)]
            except:
                pass

        print("yes")
