import time
from urllib.request import urlopen

import pymysql
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import datetime
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

df = pd.DataFrame()
session = requests.Session()
# user-agent is the most important thing to determine yes humanity or no.
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
           "Accept": "text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,*/*;q=0.8"}
url = "https://www.aircanada.com/"
req = requests.get(url, headers=headers)
driver = webdriver.Chrome(executable_path="/usr/local/bin/chromedriver")
now = datetime.datetime.now()
current_time = (str(now.hour) + ":" + str(now.minute))
current_date = (str(now.year) + "/" + str(now.month) + "/" + str(now.day))

conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock', user='root', passwd='12345678', db='mysql')
cur = conn.cursor()
cur.execute("USE Flight")

one_way = "//li[@id='tripTypeIdtripType_O']"
round_way = "//li[@id='tripTypeIdtripType_R']"
Multi_city = "//li[@id='tripTypeIdtripType_M']"


# bsObj = BeautifulSoup(req.text, "html.parser")
# bss = bsObj.findAll("a", {"href":"/us/en/aco/home/book/travel-news-and-updates/2020/covid-19.html"})
# for bs in bss:
# print(bs)


# choose one-way, round-trip, or multiple city.
def ticket_chooser(Oway):
    ticket_type = driver.find_element_by_xpath("//div[@id='tripTypeLabel']")
    ticket_type.click()
    time.sleep(1)
    ticket_type_0 = driver.find_element_by_xpath(Oway)
    ticket_type_0.click()


# input departure city
def departure(dep):
    from_ = driver.find_element_by_xpath("//input[@data-se-id='origin_0']")
    time.sleep(1)
    from_.clear()
    time.sleep(1)
    from_.send_keys(dep)
    time.sleep(1)
    from_.send_keys(Keys.ENTER)


def arrival(arr):
    to = driver.find_element_by_xpath("//input[@data-se-id='destination_0']")
    time.sleep(1)
    to.clear()
    time.sleep(1.5)
    to.send_keys(arr)
    time.sleep(1.5)
    to.send_keys(Keys.ENTER)


def departure_date(month, day):
    dep = driver.find_element_by_xpath("//input[@id='fligthDepartureDate']")
    driver.execute_script('arguments[0].click()', dep)
    time.sleep(1)
    dep.clear()
    dep.send_keys(day + "/" + month)


def search():
    button = driver.find_element_by_xpath("//input[@data-se-id='btnFlightsSearchOption2']")
    driver.execute_script('arguments[0].click()', button)
    time.sleep(15)
    print("searching!")


def compile_data():
    global df
    global dep_time
    global arr_time
    global price
    global duration

    # departure time
    dep_t = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@class='itinerary-depart-time depart-time']")))
    dep_time = [value.text for value in dep_t]

    # arrival time
    arr_t = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@class='itinerary-arrival-time arrival-time']")))
    arr_time = [value.text for value in arr_t]

    # price
    p = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@class='display-on-hover']")))
    price = [value.text for value in p]

    # duration
    d = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@class='stop-over-info stop-over-detail']")))
    duration = [value.text for value in d]

    for i in range(len(dep_time)):
        try:
            df.loc[i, 'departure_time'] = dep_time[i]
        except Exception as e:
            pass
        try:
            df.loc[i, 'arrival_time'] = arr_time[i]
        except Exception as e:
            pass
        try:
            df.loc[i, 'price'] = price[i]
        except Exception as e:
            pass
        try:
            df.loc[i, 'duration'] = duration[i]
        except Exception as e:
            pass


for i in range(8):
    url = "https://www.aircanada.com/"
    driver.get(url)
    time.sleep(5)

    ticket_chooser(one_way)
    departure('Hong Kong')
    arrival('yyz')
    departure_date("09", "07")
    search()
    compile_data()

    current_value = df.iloc[0]
    cheapest_dep_time = current_value[0]
    cheapest_arr_time = current_value[1]
    cheapest_price = current_value[2]
    cheapest_duration = current_value[3]

    msg = '\nCurrent Cheapest flight:\n\nDeparture time: {}\nArrival time: {}\nFlight duration: {}\nPrice: {}\n'.format(
        cheapest_dep_time, cheapest_arr_time, cheapest_duration, cheapest_price)
    print(msg)
    select = "SELECT * FROM flight WHERE Departure_time = %s AND Arrival_time = %s AND Duration = %s AND Price = %s"
    insert = "INSERT INTO flight (Departure_time,Arrival_time,Duration,Price) VALUES (%s, %s, %s, %s)"
    data = (str(cheapest_dep_time), str(cheapest_arr_time), str(cheapest_duration), str(cheapest_price))
    cur.execute(insert, data)
