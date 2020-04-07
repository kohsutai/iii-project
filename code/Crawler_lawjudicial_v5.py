from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import multiprocessing as mp
from pymongo import MongoClient

# 建立Mongodb collection
client = MongoClient('172.28.0.2:27017')   # python連mongodb
db = client["judicial_test"]    # 資料庫名稱
collect = db["judi"]    # collection名稱

def write_json_file(judge_id, judge_date, judge_reason, judge_content,
                                each_judgment_list, each_law_list):

    data = {'judge_id': judge_id,
            'judge_date': judge_date,
            'judge_reason': judge_reason,
            'judge_content': judge_content,
            'each_judgment_list': each_judgment_list,
            'each_law_list': each_law_list
            }
    collect.insert_one(data)

def send_condition(browser, court, reason, year, month):
    time.sleep(1)
    Select(browser.find_element_by_id('jud_court')).select_by_value('%s' % court)
    browser.find_element_by_xpath('/html/body/form/div[5]/div/div/div[2]/div[2]/table/tbody/tr[1]/td/label[1]/input').click()
    browser.find_element_by_id('dy1').send_keys('%d' % year)
    browser.find_element_by_id('dy2').send_keys('%d' % year)
    browser.find_element_by_id('dm1').send_keys('%d' % month)
    browser.find_element_by_id('dm2').send_keys('%d' % (month + 5))

    if reason == '離婚':
        browser.find_element_by_id('jud_title').send_keys('%s' % reason)
    else:
        browser.find_element_by_id('jud_kw').send_keys('%s' % reason)

    try:
        browser.find_element_by_xpath('//*[@id="btnQry"]').click()
    except:
        browser.refresh()
        send_condition(browser, court, reason, year, month)


def get_element(browser, court, reason, year, month):
    try:
        time.sleep(2)
        browser.switch_to.frame(browser.find_element_by_xpath('//*[@id="iframe-data"]'))
        browser.find_elements_by_id('hlTitle')[0].click()

        # 總資料量
        total_number = int(browser.find_element_by_id('plPager').text.split()[3])

        each_judgment_list = []
        each_law_list = []

        for i in range(total_number):
            # 找判決書內容
            try:
                time.sleep(1)
                judge_id = browser.find_elements_by_class_name('col-td')[0].text
                judge_date = browser.find_elements_by_class_name('col-td')[1].text
                judge_reason = browser.find_elements_by_class_name('col-td')[2].text
                judge_content = ' '.join(
                    browser.find_elements_by_xpath('//div[@class="text-pre text-pre-in"]')[0].text.split())

                find_targets = browser.find_elements_by_css_selector('div.panel-body ul li')
                find_laws = browser.find_elements_by_css_selector('ul.rela-law li')

                for index in range(len(find_targets)):
                    # 找歷審裁判
                    if index < len(find_targets) - len(find_laws):
                        each_judgment_list.append(find_targets[index].text)
                    # 找相關法律
                    else:
                        each_law_list.append(find_targets[index].text)

                write_json_file(judge_id, judge_date, judge_reason, judge_content, each_judgment_list, each_law_list)

            except IndexError as e:
                print(e)

            each_judgment_list.clear()
            each_law_list.clear()
            print('%s 法院 %s 已完成第 %d 年 %d ~ %d 月第 %d / %d 筆' % (
                court, reason, year, month, month + 5, i + 1, total_number))

            # 換頁
            try:
                WebDriverWait(browser, 1).until(EC.presence_of_element_located((By.ID, 'hlNext')))
                browser.find_element_by_id('hlNext').click()
            except:
                print('This is the last page')
                pass
    except Exception as e:
        print(e)

    browser.close()
    print('%d 年 %d ~ %d 月 %s 法院 Completed!!' % (year, month, month + 5, court))
    print('')


def search_result(court, reason):
    for year in range(89, 109):
        for month in range(1, 8, 6):
            url = 'https://law.judicial.gov.tw/FJUD/default_AD.aspx'
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
            cap = DesiredCapabilities.CHROME
            browser = webdriver.Remote(command_executor='http://selenium:4444/wd/hub', desired_capabilities=cap)
            
            options = webdriver.ChromeOptions()
	    options.add_argument('user-agent=%s' % user_agent)
            # options.add_argument('--headless')
            browser.get(url)
            browser.get_cookies()

            send_condition(browser, court, reason, year, month)
            get_element(browser, court, reason, year, month)


if __name__ == '__main__':
    courtlist = ['TPS', 'TPH', 'TCH', 'TNH', 'KSH', 'HLH', 'TPD', 'SLD', 'PCD', 'ILD', 'KLD', 'TYD', 'SCD', 'MLD',
                 'TCD', 'CHD', 'NTD', 'ULD', 'CYD', 'TND', 'KSD', 'CTD', 'HLD', 'TTD', 'PTD', 'PHD', ' KMH', 'LCD',
                 'KSY']

    reasonlist = ['離婚', '監護權', '夫妻共同財產']

    for court in courtlist:
        for reason in reasonlist:
            search_result(court, reason)
