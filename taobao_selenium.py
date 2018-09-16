# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 17:20:18 2018

@author: luwei
"""

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from urllib.parse import quote
from bs4 import BeautifulSoup
import pymongo

browser=webdriver.Chrome()
# 无界面模式
#chrome_options=webdriver.ChromeOptions()
#chrome_options.add_argument('--headless')
#browser=webdriver.Chrome(chrome_options=chrome_options)
wait=WebDriverWait(browser,10)

#配置信息可以单独提出到config文件，便于维护 
# from config import *
Keyword="侧透机箱"
mongo_url='localhost'
mongo_db='taobao'
mongo_collection='ComputerCase'
max_page=10


conn=pymongo.MongoClient(mongo_url)
db=conn[mongo_db]

def index_page(page):
    print('正在爬取第',page,'页')
    try:
        url='https://s.taobao.com/search?q='+quote(Keyword)
        browser.get(url)
        if page>1:
            inputpage=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager div.form > input')))
            print(type(inputpage))
            submit=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mainsrp-pager div.form > span.btn.J_Submit')))
            inputpage.clear()
            inputpage.send_keys(page)
            submit.click()

        # 判定高亮的页是否为page
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager li.item.active > span'),
                                                    str(page)))
        # 等待加载所有商品信息
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.m-itemlist .items .item')))
        get_products()

    except TimeoutException:
        index_page(page)
def get_products():
    html=browser.page_source
    # 保存源码进行提取
    # with open('source.txt','a',encoding='utf-8') as f:
    #    f.write(html)
    # html=open('source.txt',encoding='utf-8')
    # soup=BeautifulSoup(html,'lxml')
    # soup=BeautifulSoup(open('source.txt',encoding='utf-8'),'lxml')
    soup=BeautifulSoup(html,'lxml')
    divs=soup.find_all(class_="J_MouserOnverReq")
    for div in divs:
        product={
        'img':div.find(name='div',class_='pic').a.img['data-src'],
        'price':div.find(name='strong').string,
        'deal':div.find(class_="deal-cnt").string,
        'title':div.select('.title a')[0].get_text().strip(),#string 提取不了
        'shop':div.select('.shop > a')[0].get_text(),
        'addr':div.find(class_="location").string,
        }
        print(product)
        save_to_mongo(product)
        


def save_to_mongo(result):

    try:
        if db[mongo_collection].insert(result):
            print('success')
    except Exception:
        print('fail')
        
def main():    
    for i in range(1,max_page+1):
        index_page(i)
    browser.close()
        
if __name__=='__main__':
    main()












