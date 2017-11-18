# coding:utf-8
import requests
import re
import time
import random
import json
import jsonpath
import pymysql
import time
from Queue import Queue
import threading

# 11.13进行mysql数据库写入
# 同时多线程
'''
    程序需要改进地方
    1.一次性获取非常多的数据，直至自己想停。
    2.数据去重
    3.多线程
    # 4.降低耦合度
'''


class ZhihuHandler(object):
    # 遍历知乎，保存页面,计数
    count = 0
    json_num = 0
    json_limit = 10

    def __init__(self):
        # 写入数据库的内容，暂存self.get_desired_json_info_result，是一个字典
        self.get_desired_json_info_result = {}
        # further_visit获取到的完整的json
        self.response = None
        # 验证码url
        self.verification_code_url = ''
        # session_token
        self.session_token = ''
        self.selection = True
        self.authorization = ''
        self.reSearch = re.compile(r'<input type="hidden" name="_xsrf" value=.*/>')
        self.headers = {
            'Host': 'www.zhihu.com',
            'Connection': 'keep-alive',
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Content - Type': 'application / x - www - form - urlencoded;charset = UTF - 8',
        }
        self.home_page_url = 'https://www.zhihu.com/'
        # 创建与mysql数据库的连接
        self.connection = pymysql.connect(host='localhost', user='root', database='zhihu', port=3306, password='970630',
                                          charset='utf8')
        # 创建执行sql语句的cursor对象
        self.cursor = self.connection.cursor()

    # 1.访问知乎首页， 并构建一个Session对象，保存Cookie，
    # 2.获取_xsrf(主要是为了获取_xsrf),_xsrf是防止csrf攻击
    # 3.获取验证码
    def visit_home_page(self):
        print('visit_home_page')
        # 创建session对象，可以保存Cookie值
        self.session = requests.session()

        # 获取登录页面，找到需要Post的数据_xsrf
        response = self.session.get(self.home_page_url + '#signin', headers=self.headers, verify=True)
        html = response.text

        result = self.reSearch.search(html).group()
        self.csrf = result.split(' ')[-1].split('"')[1]
        self.headers['X-Xsrftoken'] = self.csrf

        # 获取验证码url
        now_time = int(time.time() * 1000)
        # 验证码类型，cn为倒立的中文，en为字母数字
        lang_list = ['en', 'cn']
        self.lang = random.choice(lang_list)
        print('验证码类型：%s' % self.lang)
        self.verification_code_url = self.home_page_url + 'captcha.gif?r=%d&type=login&lang=%s' % (now_time, self.lang)
        print('visit_home_page_finished')

    # 获取验证码，并将验证码保存到本地
    def verification_code(self):
        response = self.session.get(self.verification_code_url, headers=self.headers, verify=True)
        imgB = response.content
        with open('./verification_code/vc.gif', 'wb') as f:
            f.write(imgB)
        print('验证码已被保存到本地!')

    # post方法,登录知乎
    # 同时获取authorization
    def sign_in(self):
        self.headers['Accept'] = '*/*'
        self.headers['Origin'] = 'https://www.zhihu.com'
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.headers['Referer'] = 'https://www.zhihu.com/'

        sign_in_url = 'https://www.zhihu.com/login/phone_num'
        password = 'yangshaoxuan0630'
        phone_num = '17864291830'
        # 正确输入验证码是根据verification_code获取到的验证码做到的
        captcha = str(raw_input('请输入验证码\n')).replace(' ', '')

        data = {
            '_xsrf': self.csrf,
            'password': password,
            'captcha': captcha,
            'captcha_type': self.lang,
            'phone_num': phone_num,
        }
        response = self.session.post(sign_in_url, data=data, headers=self.headers, verify=True)
        # 发现得到的z_c0长度与浏览器的不一样，所以修改了请求头，试一下
        authorization_re = re.compile(r'z_c0=".*?"')
        self.authorization = authorization_re.search(response.headers.get('Set-Cookie')).group().split('=', 1)[
            1].replace('"', '')

        if response.status_code == 200:
            print('登录成功！状态码:%d' % response.status_code)
            return True
        else:
            print('登录失败！状态码:%d' % response.status_code)
            return False

    # 获取session_token，获取成功
    def get_session_token(self):
        # session_token只有登录成功后，response才返回，所以只有登录成功后才能获取到
        # session_token， 保持连接，获取知乎ajax内容，找了3-4个小时吧
        # 开心！
        self.session_token = ''
        response = self.session.get(self.home_page_url + '#signin', headers=self.headers, verify=True)
        if response.status_code != 200:
            self.selection = False
            return
        with open('./html/hello.html', 'w') as f:
            f.write(response.text.encode('utf-8'))
        # re匹配session_token
        session_token_re = re.compile(r'session_token=.*?&amp')
        result = session_token_re.search(response.text).group()
        self.session_token = result.split('=')[1].split('&')[0]

    # 读取ajax，只要下拉，然后出现新的信息，而且页面url没变，这就是ajax
    # further_visit用于获取完整的json数据保存到self.response
    def further_visit(self):
        source_url = 'https://www.zhihu.com/api/v3/feed/topstory?'

        # 下面代码需要只执行一次即可
        # 待解决
        if ZhihuHandler.count == 0:
            self.headers['Accept'] = 'application/json, text/plain, */*'
            self.headers['authorization'] = 'Bearer ' + self.authorization
            self.headers['X - API - VERSION'] = '3.0.53'
            self.headers['X-Xsrftoken'] = self.csrf

        after_id = 9 + ZhihuHandler.count * 10
        post_query_string = {
            'action_feed': True,
            'limit': ZhihuHandler.json_limit,
            'session_token': self.session_token,
            'action': 'down',
            'after_id': after_id,
            'desktop': 'true',
        }
        self.response = self.session.get(source_url, params=post_query_string, headers=self.headers, verify=True)
        print('further_visit')
        print(self.response.status_code)
        if self.response.status_code != 200:
            self.selection = False
        else:
            self.selection = True
            print('第%d次json获取' % ZhihuHandler.count)

    # 从further_visit获取到的完整json数据self.response 读取想要的内容,
    # 保存self.get_desired_json_info_result变量
    def get_desired_json_info(self):
        json_html = self.response.text.decode('UTF-8')
        json_object = json.loads(json_html, encoding='UTF-8')
        print json_html

        # 作者姓名
        author_names = jsonpath.jsonpath(json_object, '$..target.author.name')

        # 该回答属于什么话题，情感，运动。。。话题同时可以有多个
        # 因为每个topic属于actors，所以可以通过获取actors数组的长度来确定有几个主题。
        actors_array = jsonpath.jsonpath(json_object, '$..data..actors')
        # 记录一个回答属于话题的个数
        topic_count = []
        for item in actors_array:
            item = str(item).replace('{', '').replace('}', '')
            follow_interest_count = item.count(u'follow_interest')
            topic_count.append(follow_interest_count)

        # 获取话题
        topics = jsonpath.jsonpath(json_object, '$..actors..name')
        print topic_count
        for i in range(0, len(topic_count)):
            if topic_count[i] > 1:
                for j in range(i, (topic_count[i] + i - 1)):
                    topics[i] = topics[i] + ' ' + topics[j + 1]
                    if j != i:
                        del topics[j]

        # 回答内容
        # contents = jsonpath.jsonpath(json_object, '$..data..target.[content, detail]')
        # 回答的内容有可能被包含在target的detail中和description
        # details = jsonpath.jsonpath(json_object, '$..data..target.detail')
        contents = jsonpath.jsonpath(json_object, '$..data..target.[content,detail,description]')


        # 提问的标题
        titles = jsonpath.jsonpath(json_object, '$..data..target.question.title')
        if len(titles) < len(author_names):
            titles_many = jsonpath.jsonpath(json_object, '$..data..target..title')
            titles_little = jsonpath.jsonpath(json_object, '$..data..target.title')
            for item in titles_little:
                titles_many_index = titles_many.index(item)
                titles.insert(titles_many_index, item)

        # print(topics)
        # print(titles)
        for i in range(0, len(author_names)):
            # tiltes出现问题
            self.get_desired_json_info_result[ZhihuHandler.json_num] = [topics[i], titles[i], author_names[i],
                                                                        contents[i]]
            ZhihuHandler.json_num += 1

    # 将get_desired_json获取的想要的数据self.get_desired_json_info_result（这是一个字典）写入mysql 数据库
    def write_json_info_mysql(self):
        tmp_json_mysql = []
        sql = 'insert into jsoninfo(zhihuid, topic, title, author_name, content) VALUES (%s, %s, %s, %s, %s)'
        for key, values in self.get_desired_json_info_result.items():
            tmp_json_mysql.append(key)
            for value in values:
                tmp_json_mysql.append(value)
            flag = self.cursor.execute(sql, tmp_json_mysql)
            if flag != 0:
                self.connection.commit()
            print('一条数据写入成功！')
            tmp_json_mysql = []
        self.get_desired_json_info_result = {}

    def main(self):
        while True:
            if ZhihuHandler.count == 0:
                self.selection = raw_input("开始遍历知乎？True|False\n")
                if str(self.selection).lower() == 'true':
                    self.visit_home_page()
                    self.verification_code()
                    self.selection = self.sign_in()
                    self.get_session_token()
                else:
                    break
            else:
                # self.selection = raw_input("是否继续遍历知乎？True|False\n")
                # 稍稍休息一下，免得被封了，不要太嚣张
                time.sleep(6)
                self.selection = True
            if str(self.selection).lower() == 'true':
                print('=' * 30)
                print('\n')
                print('开始第%d次遍历知乎，每次获取10条json' % ZhihuHandler.count)
                # 用于每次获取10条json流程控制
                main_handler_number = 10
                while main_handler_number:
                    print('执行第%d次' % main_handler_number)
                    main_handler_number -= 1
                    self.further_visit()
                    self.get_desired_json_info()
                    self.write_json_info_mysql()
                    ZhihuHandler.count += 1
                print('=' * 30)
                print('\n')
            else:
                break


if __name__ == '__main__':
    zhihu = ZhihuHandler()
    zhihu.main()
