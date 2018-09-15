# -*- coding: utf-8 -*-
"""
Created on Tue Sep 11 22:12:57 2018

@author: luwei

re (.*?  [\s\S]*? )
pattern = re.compile('<p class="name">[\s\S]*?title="([\s\S]*?)"[\s\S]*?<p class="star">([\s\S]*?)</p>[\s\S]*?<p class="releasetime">([\s\S]*?)</p>')
多进程
from multiprocessing import Pool
# 创建进程池
pool = Pool()
# 第一个参数是函数，第二个参数是一个迭代器，将迭代器中的数字作为参数依次传入函数中
pool.map(crawl, [i*10 for i in range(10)])
pool.close()
pool.join()

同时写入文件需要加锁
from multiprocessing import Manager
import functools
偏函数functools.partial(函数，参数) 顺序指定函数的参数，改变原函数的参数数量

"""


import  requests
import json
import re
from bs4 import BeautifulSoup
from lxml import etree
import time
import random
from requests.exceptions import RequestException

from multiprocessing import Pool
from multiprocessing import Manager
import functools

def get_one_page(url):
    '''提取一页源码'''
    try:
        headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                }
        resp=requests.get(url,headers=headers)
        if resp.status_code==200:
            return resp.text
        return None
    except RequestException:
       return None

# re解析
def parse_one_page(html):
    re_str='''<dd>.*?board-index.*?>(.*?)</i>.*?data-src="(.*?)".*?name.*?title="(.*?)".*?star.*?>(.*?)</p>.*?releasetime">(.*?)</p>.*?class="integer">(.*?)</i><i class="fraction">(.*?)</i>'''
    pattern=re.compile(re_str,re.S)
    items=re.findall(pattern,html)
    for item in items:
        yield ({'index':item[0],
               'image':item[1],
               'title':item[2],
               'actor':item[3].strip(),
               'time':item[4][5:],
               'score':item[5]+item[6]
                })
#bs4解析 
def parse_bs4(html):
    soup=BeautifulSoup(html,'lxml')
    dds=soup.find_all(name="dl",class_="board-wrapper")[0].find_all(name='dd')
    for dd in dds:
        yield({
        'index':dd.find(name='i').string,
        'img':dd.find(class_="board-img")['data-src'],
        'title':dd.div.a.attrs['title'],
        'actor':dd.find(class_="star").string.strip(),
        'time':dd.find(class_="releasetime").string[5:],
        'score':dd.select('.score i')[0].string+dd.select('.score i')[1].string,
        })
#xpath解析 
def parse_xpath(html):
    html_xp=etree.HTML(html)
#    print(type(html_xp))
#    r1=html_xp.xpath("//dl[@class='board-wrapper']/dd")
    for i in range(1,11):
        yield({
        'index':html_xp.xpath("//dl[@class='board-wrapper']/dd[%d]/i/text()"%i)[0],
        'img':html_xp.xpath("//dl/dd[%d]/a/img[2]/@data-src"%i)[0],
        'title':html_xp.xpath("//dl/dd[%d]/div/div/div[1]/p[1]/a/text()"%i)[0],
        'actor':html_xp.xpath("//dl/dd[%d]/div/div/div[1]/p[2]/text()"%i)[0].strip(),
        'time':html_xp.xpath("//dl/dd[%d]/div/div/div[1]/p[3]/text()"%i)[0][5:],
        'score':html_xp.xpath("//dl/dd[%d]/div/div/div[2]/p/i[1]/text()"%i)[0] + \
                html_xp.xpath("//dl/dd[%d]/div/div/div[2]/p/i[2]/text()"%i)[0],
        })
    
#写入文件
def write_to_file(content):
    with open('maoyan100.txt','a',encoding='utf-8') as f:
#        print(type(json.dumps(content)))
        f.write(json.dumps(content,ensure_ascii=False)+'\n')

# 爬取
def crawl(offset):
    url='http://maoyan.com/board/4?offset='+str(offset)
    html=get_one_page(url)
    for item in parse_one_page(html):
        write_to_file(item)
    for item in parse_bs4(html):
        write_to_file(item)
    for item in parse_xpath(html):
        write_to_file(item)

def crawlPage(lock, offset):
   # 得到真正的URL
   url = "http://maoyan.com/board/4?offset="+str(offset)
   # 下载页面
   html = get_one_page(url)
   # 提取信息,写入到本地文件系统或者数据库
   for item in parse_one_page(html):
       lock.acquire()
       write_to_file(item)#将数据写到本地的文件系统中
       lock.release()
    
if __name__=="__main__":
    # for i in range(10):
    #     crawl(i*10)
    #     time.sleep(random.randint(1,3))

    manager = Manager()
    lock = manager.Lock()
    # 使用一个函数包装器
    pcrawlPage = functools.partial(crawlPage, lock)
    pool = Pool()
    pool.map(pcrawlPage, [i*10 for i in range(10)])# 分配给进程池任务序列
    pool.close()
    pool.join()

    print("Finished")
