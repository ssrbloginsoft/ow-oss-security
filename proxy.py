from msilib.schema import Error
from termcolor import colored
import requests
from bs4 import BeautifulSoup

proxies = []


def get_valid_proxy(proxy):  # format of items e.g. '128.2.198.188:3124'
    proxy_obj = {
        'http': f'http://{proxy}'
    }

    try:
        requests.get('https://google.com', timeout=(5, 5), proxies=proxy_obj)
    except Exception as e:
        #logging.info("Test error")
        print(e)
        pass
    else:
        proxies.append(proxy)
        return(proxy)


def proxies_grab():
    html_doc = requests.get("https://www.sslproxies.org/").text
    soup = BeautifulSoup(html_doc, 'html.parser')
    tbody = soup.find("tbody")

    for tr in tbody:
        ip_td = list(tr)[0].get_text()
        get_valid_proxy(ip_td)

    return proxies


# print(proxies_grab())
