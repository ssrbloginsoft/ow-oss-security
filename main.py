from time import sleep
from typing import List
import requests
from requests.exceptions import ProxyError, ConnectionError, Timeout
from proxy import proxies_grab
from utils import diff_list, validate_url
from lxml.html import parse
import urllib
import os
from pymongo import MongoClient

static_proxies = ['133.242.237.138', '31.192.141.1', '164.155.149.1', '200.105.215.18', '8.218.69.97', '212.200.44.246', '151.106.17.123', '151.106.13.219', '164.155.146.31', '164.155.150.1', '51.15.166.107', '151.106.17.126', '40.69.60.146', '164.155.147.1', '164.155.147.31', '103.137.63.209', '45.77.234.105', '117.20.216.218', '217.30.173.108', '103.155.84.18', '94.23.241.200', '5.39.189.39', '157.100.12.138', '138.219.245.17', '190.97.226.236', '41.65.251.84', '176.9.162.107', '103.214.9.13', '154.236.177.101', '37.120.192.154', '61.198.85.127', '103.152.100.155', '41.65.236.43', '20.81.62.32', '5.189.184.6', '183.91.0.121', '145.239.169.45', '125.190.22.211', '203.189.137.180', '121.40.162.184', '145.239.169.40', '103.142.200.58', '154.236.184.77', '5.16.0.97', '200.69.74.166', '95.217.72.247', '101.51.139.179', '184.95.0.218', '41.65.236.57',
                  '118.175.244.111', '12.88.29.66', '187.188.167.30', '188.166.228.110', '61.9.34.46', '103.152.100.183', '201.222.45.64', '125.25.32.96', '213.212.210.250', '181.129.2.90', '91.151.89.32', '156.200.116.68', '183.88.232.207', '5.9.112.247', '45.174.79.189', '91.106.64.2', '161.49.91.13', '190.94.199.14', '157.100.53.100', '45.239.123.99', '45.118.151.25', '50.232.250.157', '31.3.169.53', '95.142.223.24', '67.73.184.178', '54.183.230.101', '45.230.225.1', '181.118.158.131', '177.234.164.50', '216.176.187.99', '80.244.226.92', '196.219.202.74', '34.70.148.223', '45.70.14.58', '155.93.96.210', '200.92.152.50', '188.133.158.145', '190.111.203.179', '180.210.178.30', '41.128.148.76', '80.244.229.102', '95.140.31.39', '201.71.2.107', '41.174.179.147', '102.165.127.85', '95.217.20.255', '165.16.30.161', '201.71.2.41', '45.4.88.135', '41.65.236.44', '115.74.213.139']


class Page():

    def __init__(self, url: str = None, max_retries: int = 3, connect_timeout: int = 10, read_timeout: int = 10) -> None:
        self.url = url
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self._counter = 0
        self._retries = 0
        self._timeout = (self.connect_timeout, self.read_timeout)

        self._proxies = static_proxies
        self._proxy = {
            'http': f'http://{self._proxies[self._counter+2]}'
        }

        # if validate_url(self.url):
        #     raise Exception("Invalid URL!")

    def get_page(self):
        try:
            res = requests.get(self.url, timeout=self._timeout,
                               proxies=self._proxy, stream=True)
            res.raw.decode_content = True
            tree = parse(res.raw)

            if self._retries != 0:
                self._retries = 0

            print(f"==> Successfully fetched the url: {self.url}")

            return tree
        except (ProxyError, Timeout) as err:
            print("==> Proxy Error: ", err)
            return self.retry()
        except ConnectionError as err:
            sleep(5)
            return self.retry()
        except Exception as err:
            print("==> Error occurred while processing the page: ", err)

    def retry(self):
        if(len(self._proxies) == self._counter+1):
            self._proxies = diff_list(self._proxies, proxies_grab())
            self._counter = 0
            self._retries += 1
        else:
            self._counter += 1

        self._proxy['http'] = f'http://{self._proxies[self._counter]}'

        if (self._retries < self.max_retries):
            print(f'==> Refetching the page: {self.url}')
            return self.get_page()
        else:
            sleep(5)
            print(f'==> Reached max retry limit: {self.url}')
            return self.get_page()
            # raise Exception(
            #     f"==> Reached max retry limit: {self.max_retries}")


class Plugin():
    def __init__(self, name: str, page: Page, handler) -> None:
        self.name = name
        self.page = page
        self.handler = handler

    def process(self):
        html_doc = self.page.get_page()
        return self.handler(html_doc)


class Scrapper():
    def __init__(self) -> None:
        self._plugins: List[Plugin] = list()

    def create_and_register_plugin(self, name: str, page: Page, handler):
        plugin = Plugin(name=name, page=page, handler=handler)
        self._plugins.append(plugin)

    def execute_all(self):
        for plugin in self._plugins:
            yield plugin.process()


def connect_to_db():
    username = urllib.parse.quote_plus("")
    password = urllib.parse.quote_plus("")
    host = 'localhost'
    uri = 'mongodb'
    client = MongoClient('%s://%s:%s@%s' %
                         (uri, username, password, host), maxPoolSize=10000)
    print("==> Connected to db")
    db = client['oss']
    return db
