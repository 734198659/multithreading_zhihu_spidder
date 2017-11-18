# multithreading_zhihu_spidder
Python2.7 爬取知乎

项目功能介绍：
---------
   这个爬虫是用于爬取知乎首页https://www.zhihu.com/ 下拉时返回的json数据。<br>
   但是项目功能并不完整：<br>
       1）只能爬取2000条数据，一旦超过2000条，抛出异常（待解决，更改日期未定）<br>
       2）毫无容错性<br>
       3）数据并未去重<br>
<br><br><br>

项目所需技术：
---------
    1.Python版本：<br>
         Python 2.7<br>
    2.数据库：<br>
         mysql数据库<br>
    3.json解析：<br>
         jsonpath<br>
         re<br>
    4.队列：<br>
         Queue模块<br>
    5.线程：<br>
         threading模块<br>
    6.requests模块
<br><br><br>

项目文件介绍：
---------
    1.main.py 是一个单进程单线程的爬虫<br>
    2.multithreading.py 是一个单进程多线程的爬虫<br>
    3.verification_code文件夹用于存放获取到的验证码<br>
    4.中文验证码输入.txt 是要求输入倒立的中文验证码所对应的输入内容<br>
    5.log文件夹原是用于存储日志<br>
    6.json文件夹是上一个版本存储获取到的json数据<br>
    7.html文件夹是上一个版本获取响应的网址内容<br>
<br><br><br>

其他：
---------
    待补充
