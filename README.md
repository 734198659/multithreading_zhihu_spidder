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
    0.Python版本：<br>
         Python 2.7<br>
    1.数据库：<br>
         MySQL<br>
    2.json解析：<br>
         jsonpath<br>
         re<br>
    3.队列：<br>
         Queue模块<br>
    4.线程：<br>
         threading模块<br>
    5.urllib2
<br><br><br>

项目文件介绍：
---------
    main.py 是一个单进程单线程的爬虫<br>
    multithreading.py 是一个单进程多线程的爬虫<br>
    中文验证码输入.txt 是要求输入倒立的中文验证码所对应的输入内容<br>
<br><br><br>
