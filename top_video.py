"""This program crawls meta data of short videos from kolranking.com.

Before running this program, please:
1. install chromedriver that is compatible with your Chrome browser from
http://chromedriver.chromium.org/. After it's unzipped, cope the path of
the chromedriver to 'browser_path' in the code.
2. create an account at kolranking.com
3. find the profile path of your Chrome browser and copy to 'profile' in
the code if you want auto login next time
"""
import csv
import time
from inflect import engine
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


# setting
browser_path = r'path_to_your_chromedriver'
login_url = 'https://kolranking.com/login'
account, pw = 'your_account', 'your_password'
url_home = 'https://kolranking.com/home'  # url after logged in
original_url = 'https://kolranking.com/douyin/videos?ot=' \
               'DESC&order=digg_count&date=2019-02-03&des=&page='
from_page = 1  # the first page to crawl data from
end_page = 50  # the last page to crawl data from
time_now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
data_name = 'top{num}_{stamp}.csv'.format(num=(end_page-from_page+1)*10,
                                          stamp=time_now)
# use my Chrome options for auto login
options = webdriver.ChromeOptions()
profile = r'path_to_your_chrome_profile'
options.add_argument('user-data-dir='+profile)
auto_login = False  # True - use my profile
if auto_login:
    br = webdriver.Chrome(browser_path, chrome_options=options)
else:
    br = webdriver.Chrome(browser_path)


def code_verification(browser):
    """check if need code verification and type in if need
    """
    boxes = browser.find_elements_by_xpath("//input[@type='text']")
    buttons = browser.find_elements_by_xpath("//button[@type='submit']")
    bx_num, bt_num = len(boxes), len(buttons)
    print('Number of text boxes is {}, '.format(bx_num),
          'Number of buttons is {}. '.format(bt_num), end='')
    # need code verification if there is a text box and a submit button
    if bx_num == 1 and bt_num == 1:
        print('Need code verification')
        for b in boxes:
            b.send_keys(input('Please enter the code: '))
        for bt in buttons:
            bt.submit()
        code_verification(browser)
    else:
        print('Code verification passed')


def login(link, browser, name, code, home):
    """login to account in order to view pages and data
    """
    try:
        browser.get(link)
    except TimeoutException:
        print('Time Out')
    time.sleep(5)
    print('Typing in username ... ', end='')
    username = browser.find_element(By.ID, 'email')
    username.send_keys(name)
    print('Done')
    print('Typing in password ... ', end='')
    password = browser.find_element(By.ID, 'password')
    password.send_keys(code)
    print('Done')
    print("Checking 'RememberMe' box ... ", end='')
    cbs = browser.find_elements_by_xpath("//input[@name='remember']")
    for cb in cbs:
        cb.click()
        if cb.is_selected():
            print('Done')
        else:
            print('Not checked')
    print('Logging in ... ')
    time.sleep(0.01)
    buttons = browser.find_elements_by_xpath("//button[@type='submit']")
    for b in buttons:
        b.submit()
    c_url = browser.current_url
    if c_url == home:
        code_verification(browser)
        print('Logged in!')
    else:
        print('Not logged in, check the browser to see what happens')
    time.sleep(5)


def load_page(link, browser):
    browser.get(link)
    # check if need code verification or not
    code_verification(browser)
    print('Page loaded')
    return browser.page_source


def get_page_content(link, browser):
    html = load_page(link, browser)
    # load the link again if '504 Gateway Time-out' appears
    times = 0
    while '504 Gateway Time-out' in html:
        if times == 3:
            print('Give up after reloading {} times'.format(times))
            break
        times += 1
        print("'504 Gateway Time-out' appears. "
              + "Reload for the {} time.".format(engine().ordinal(times)))
        html = load_page(link, browser)
    if '下一页' in html:
        next_webpage = True
    else:
        next_webpage = False
        print('No more pages after this.')
    bs = BeautifulSoup(html, 'lxml')
    return bs, next_webpage


def parser_to_csv(bs):
    table = bs.find('table', class_='table user-list')
    results = table.find_all('tr')
    rows = []
    for result in results:
        data = result.find_all('td')
        if len(data) == 0:
            continue
        num = data[0].getText().strip()
        author = data[2].getText().strip()
        desc = data[3].getText().strip()
        like_num = data[4].getText().strip()
        comm_num = data[5].getText().strip()
        share_num = data[6].getText().strip()
        rows.append([num, author, desc, like_num, comm_num, share_num])
    for row in rows:
        print(row)
    with open(data_name, 'a', encoding='utf-8', newline='') as csv_file:
        writer = csv.writer(csv_file)
        for num, author, desc, like_num, comm_num, share_num in rows:
            writer.writerow([num.encode('gbk', 'ignore').decode('gbk'),
                             author.encode('gbk', 'ignore').decode('gbk'),
                             desc.encode('gbk', 'ignore').decode('gbk'),
                             like_num.encode('gbk', 'ignore').decode('gbk'),
                             comm_num.encode('gbk', 'ignore').decode('gbk'),
                             share_num.encode('gbk', 'ignore').decode('gbk'),
                             datetime.now()])


# run #
# log in
login(login_url, br, account, pw, url_home)
# crawl and save data
next_page = True
for i in range(from_page, end_page+1):
    url = original_url + str(i)
    if next_page:
        print('Crawling the {} page: '.format(engine().ordinal(i)) + url)
        soup, next_page = get_page_content(url, br)
        parser_to_csv(soup)
        time.sleep(5)  # mimic human speed
    if not next_page or i == end_page:
        print('Finished. Crawled data from {} pages.'.format(
            end_page-from_page+1))
        br.close()
