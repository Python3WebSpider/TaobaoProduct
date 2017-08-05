import re
import pymongo
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from pyquery import PyQuery as pq
from config import *

browser = webdriver.Chrome()

wait = WebDriverWait(browser, 10)

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def search():
    try:
        print('正在查询')
        browser.get('https://www.taobao.com')
        input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#q')))
        submit = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#J_TSearchForm .search-button .btn-search')))
        input.send_keys(KEYWORD)
        submit.click()
        total = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager .total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    print('当前翻页', page_number)
    try:
        input = wait.until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="mainsrp-pager"]/div/div/div/div[2]/input')))
        submit = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="mainsrp-pager"]/div/div/div/div[2]/span[3]')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text(),
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(2):
            print('存储到MongoDB成功', result)
    except Exception:
        print('存储到MongoDB失败', result)


def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(1, total + 1):
        next_page(i)
    browser.close()


if __name__ == '__main__':
    main()
