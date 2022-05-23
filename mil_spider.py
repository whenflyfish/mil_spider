import requests
from datetime import datetime
import urllib.request
import urllib
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from threading import Thread
import threading
import socket
import csv
import json
import time
import os
from tqdm import tqdm
from requests.adapters import HTTPAdapter
'''
情报源
情报源注册时长
情报源关注着数目
文章标题
文章作者
文章发布时间
爬取时间
文章正文
阅读数
转发数
链接
'''


def connectchrome():
    options = Options()
    options.add_argument('--no-sandbox')  # 禁用沙箱【不加在liunx下会报错】
    # options.add_argument('headless')  # 设置option
    options.add_argument('log-level=3')
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox");
    options.add_argument("--disable-dev-shm-usage");
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
    })
    driver.maximize_window()
    sleep(2)
    return driver


class ZGJSProcessor:
    # website:http://www.js7tv.cn/
    def __init__(self):
        self.url = 'https://eng.mil.ru/en/news_page/country.htm'

        now_time = int(time.time())
        # 为了方便调试把时间固定
        #self.day_time = time.mktime(time.strptime("2022-03-17", "%Y-%m-%d"))
        self.day_time = time.mktime(time.strptime(time.strftime("%Y-%m-%d", time.localtime(now_time)), "%Y-%m-%d"))
        self.news_url_list = []
        self.head = {'User-Agent': 'Mozilla / 5.0(Windows NT 10.0; Win64; x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 101.0.4951.67 Safari / 537.36'}
        # Mozilla / 5.0(Windows NT 10.0; Win64; x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 101.0.4951.67 Safari / 537.36
        self.path = 'D:\data\spider\mil'
        basename = 'mil' + time.strftime("%Y%m%d", time.localtime(now_time))
        self.path = os.path.join(self.path, basename)
        self.image_name = 0
        self.video_name = 0
        self.file_download_timeout = [20, 50, 100]

    def get_driver(self):
        driver = connectchrome()
        print("打开浏览器")
        return driver

    # 获取网页url
    def get_news_url_list(self, driver, url):
        try:
            driver.get(url)
        except WebDriverException:
            print("网页打开错误，重新尝试")
            # sleep(20)
            # self.get_news_url_list(driver,url)
        flag = 1
        #try:
        url_list = driver.find_elements(By.XPATH, "//div[@class='newsitem']")
        for element in url_list:
            # print("element.is_displayed: ", element.is_displayed())
            child_element = element.find_elements_by_css_selector("*")
            url = child_element[1].get_attribute("href")
            # print(url)
            t = child_element[0].get_attribute('textContent')[0:10]
            timeArray = time.mktime(time.strptime(t, "%d.%m.%Y"))
            # print(timeArray)
            if int(self.day_time) > int(timeArray):
                flag = 0
                break
            self.news_url_list.append(url)
            #print(t)
        if flag == 1:
            pages_num = driver.find_element(By.XPATH, "//a[@class='pagenava']").get_attribute('textContent')
            # print("pages_num: ", pages_num)
            url_pages = driver.find_elements(By.XPATH, "//a[@class='pagenav']")
            # print("url_pages: ", url_pages)
            url_page = url_pages[int(pages_num)].get_attribute("href")
            # print("下一页网址: ", url_page)
            #driver.quit()
            self.get_news_url_list(driver, url_page)
        sleep(3)
        #except:
            #print("网址获取出错")
        return self.news_url_list

    # 获取文本、图片地址、视频地址
    def get_data_list(self, news_url_list):
        data_list = []
        img_list = []
        video_list = []
        for news_url in news_url_list:
            try:
                dic = {}
                response = requests.get(news_url, headers=self.head).text
                tree = etree.HTML(response)
                # 情报源
                dic["情报源"] = "俄罗斯国防部"
                # 情报源注册时长（空）
                dic["情报源注册时长"] = ""
                # 情报源关注者数目(空)
                dic["情报源关注者数目"] = ""
                # 文章标题
                dic["标题"] = self.is_content(tree.xpath("//div[@id='center']/h1/text()"))
                print("文章标题: ", dic["标题"])
                # 文章作者
                dic["作者"] = self.is_content(tree.xpath("//a[@class='date']/text()"))
                print("文章作者: ", dic["作者"])
                # 文章发布时间
                publish_time = tree.xpath("//*[@id='center']/span/text()")
                dic["发布时间"] = datetime.strptime(self.is_content(publish_time), "%d.%m.%Y (%H:%M)")
                print("文章发布时间: ", dic["发布时间"])
                # 爬取时间
                now = datetime.now()
                dic["爬取时间"] = now.strftime('%Y-%m-%d %H:%M:%S')
                # 文章正文
                content = ""
                temp = tree.xpath('//*[@id="center"]/p')
                for t in temp:
                    content += t.xpath('string(.)')
                dic["正文"] = content
                print("正文: ", dic["正文"])
                # 阅读数
                dic["阅读数"] = ""
                # 转发数
                dic["转发数"] = ""
                # 链接
                dic["url"] = news_url
                data_list.append(dic)
                # 获取滚动图片
                parent_img = tree.xpath("//*[@class='ad-thumb-list']/li")
                for i in parent_img:
                    url = "https://eng.mil.ru/" + self.is_content(i.xpath("./a/@href"))
                    img_list.append([url, dic["标题"]+ "_" + str(self.image_name)])
                    self.image_name = self.image_name + 1
                # 获取固定图片
                if len(parent_img) == 0:
                    img = tree.xpath("//img[@class='image0']/@src")
                    if len(img)!=0:
                        url = "https://eng.mil.ru/" + self.is_content(img)
                        img_list.append([url, dic["标题"]+ "_" +str(self.image_name)])
                        self.image_name = self.image_name + 1
                # 获取视频url
                url = tree.xpath("//video/*/@src")
                for u in url:
                    video_list.append([u, dic["标题"] + "_" + str(self.video_name) + '.mp4'])
                    self.video_name = self.video_name + 1
            except:
                print("当前文章爬取出错，跳过")
        return data_list, img_list, video_list

    def save_data(self, data_list):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:8]
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        text_name = "俄罗斯国防部_" + str(timestamp) + ".json"
        paths = os.path.join(self.path, text_name)
        with open(paths, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data_list, indent=2,ensure_ascii=False,default=str))

    # 多线程下载图片
    def download_img(self, img_url, title, semlock):
        # try:
        semlock.acquire()
        paths = os.path.join(self.path, 'images/')
        if not os.path.exists(paths):
            os.makedirs(paths)
        opener = urllib.request.build_opener()  # 实例化一个OpenerDirector
        opener.addheaders = [('User-Agent','Mozilla / 5.0(Windows NT 10.0; Win64; x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 101.0.4951.67 Safari / 537.36')]  # 添加header,注意格式
        urllib.request.install_opener(opener)  # 将OpenerDirector装进opener
        urllib.request.urlretrieve(img_url, '{0}{1}.jpg'.format(paths, str(title)))
        print(img_url, " 下载完成")
        semlock.release()
        # except:
        #     print(img_url, " 爬取失败")

    def download_video(self, video_url, title,semlock):
        # print("爬取视频")
        # response = requests.get('https://eng.mil.ru/en/news_page/country/more.htm?id=12413390@egNews', headers=self.head).text
        # tree = etree.HTML(response)
        # url = tree.xpath("//video/*/@src")

        #semlock.acquire()
        #try:
        paths = os.path.join(self.path, 'video/')
        if not os.path.exists(paths):
            os.makedirs(paths)
        paths = paths + title
        s = requests.Session()
        # 如果失败重试5次
        s.mount(video_url,
                HTTPAdapter(max_retries=self.file_download_timeout[0]))
        downloaded = requests.get(video_url, stream=True,headers=self.head,timeout = (self.file_download_timeout[1],self.file_download_timeout[2]))
        # 获取视频总长度
        length = float(downloaded.headers['content-length'])
        with open(paths, 'wb') as f:
            # f.write(downloaded.content)
            '''
            使用手动设置更新
            total 设置总大小
            initial 当前操作文件的大小
            desc 进度条前的描述
            ncols=120设置进度条显示长度  
            nit_scale 如果设置，迭代的次数会自动按照十、百、千来添加前缀，默认为false
            '''
            pbar = tqdm(total=length, initial=os.path.getsize(paths), unit_scale=True, desc=paths, ncols=120)
            for chuck in downloaded.iter_content(chunk_size=512):
                f.write(chuck)
                # 手动更新的大小
                pbar.update(512)
            #semlock.release()
        # except:
        #     print(video_url," 爬取失败")

    def is_content(self, list):
        if len(list) == 0:
            return ""
        else:
            return str(list[0])


    def crawler(self):
        driver = self.get_driver()
        news_url_list = self.get_news_url_list(driver, self.url)
        print("网址个数：", len(news_url_list))
        driver.quit()
        data_list, img_list, video_list= self.get_data_list(news_url_list)
        self.save_data(data_list)
        # 最大线程数
        max_connections = 3
        semlock = threading.BoundedSemaphore(max_connections)
        for img in img_list:
            print("图片url : ", img[0], img[1])
            t = threading.Thread(target=self.download_img, args=(img[0], img[1], semlock))
            t.start()
            time.sleep(1)
        for v in video_list:
            print("视频url : ", v[0], v[1])
            # t = threading.Thread(target=self.download_video, args=(v[0], v[1], semlock))
            # t.start()
            # time.sleep(1)
            self.download_video(v[0],v[1],semlock)



    def crawler_keyword(self,keyword = "china"):
        driver = self.get_driver()
        url = "https://eng.mil.ru/en/news_page/country.htm"
        try:
            driver.get(url)
        except WebDriverException:
            print("网页打开错误，重新尝试")
        driver.find_element(By.XPATH, "//input[@class='searchfield']").send_keys(keyword)
        time.sleep(3)
        driver.find_element(By.XPATH, "//input[@class='searchbutton']").click()
        time.sleep(3)
        list = driver.find_elements(By.XPATH, "//*[@id='center']/table/tbody/tr")
        url_list = []
        for i in list:
            #print(i.get_attribute('textContent'))
            url = i.find_element(By.TAG_NAME,'a').get_attribute("href")
            print("url: ",url)
            url_list.append(url)
        data_list, img_list, video_list = self.get_data_list(url_list)
        self.save_data(data_list)
        # 最大线程数
        max_connections = 3
        semlock = threading.BoundedSemaphore(max_connections)
        for img in img_list:
            print("图片url : ", img[0], img[1])
            t = threading.Thread(target=self.download_img, args=(img[0], img[1], semlock))
            t.start()
            time.sleep(1)
        for v in video_list:
            print("视频url : ", v[0], v[1])
            # t = threading.Thread(target=self.download_video, args=(v[0], v[1], semlock))
            # t.start()
            # time.sleep(1)
            self.download_video(v[0], v[1], semlock)


if __name__ == '__main__':
    myZGJScrawler = ZGJSProcessor()
    myZGJScrawler.crawler_keyword()
