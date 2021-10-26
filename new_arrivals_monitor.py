"""
Queries just for shoes. If any new items that weren't there before. Push.

"""

from datetime import datetime
from json import loads, load, dumps

import httpx
import requests

from utils.tools import print_req_info

headers = {
    'Connection': 'keep-alive',
    'x-algolia-agent':
        'Algolia for JavaScript (3.35.1); Browser (lite); react (16.9.0); react-instantsearch (5.7.0); '
        'JS Helper (2.28.0)',
    'x-algolia-application-id': '3JYJSOXZO1',
    'x-algolia-api-key': '2da2a6f7496eed8347cd476da1a006b0'
}

params = (
    ('x-algolia-agent',
     'Algolia for JavaScript (3.35.1); Browser (lite); react (16.9.0); react-instantsearch (5.7.0); JS Helper (2.28.0)'),
    ('x-algolia-application-id', '3JYJSOXZO1'),
    ('x-algolia-api-key', '2da2a6f7496eed8347cd476da1a006b0'),
)
facets = ["final_price.en", "attr_size_shoe_eu.en"]

# @todo - we can search the entire thing in here with more `requests` items.
# @todo - we can use `filters` to just search for shoes. Then search for changes.
    # all in one req. Could have like 10s retry.
json = {
    "requests": [
        {
            "indexName": "01live_flae_en",
            "params": 'query='
                      '&hitsPerPage=999'
                      '&page=0'
            '&filters='
                      '(field_category_name.lvl1: "Men\'s > Shoes") OR'
                      '(field_category_name.lvl1: "Women\'s > Shoes") OR'
                      '(field_category_name.lvl2: "Kids\' > 8+ Years > Shoes") OR'
                      '(field_category_name.lvl2: "Kids\' > 4 to 8 Years > Shoes") OR'
                      '(field_category_name.lvl2: "Kids\' > Upto 4 Years > Shoes")'

        }
    ]
}


def send_req():
    out = []

    # get data from both pages
    for num in range(2):
        json["requests"][0]["params"] = json["requests"][0]["params"].replace('&page=0', f'&page={num}')
        response = httpx.post('https://3jyjsoxzo1-dsn.algolia.net/1/indexes/*/queries',
                              headers=headers,
                              params=params,
                              json=json)
        print_req_info(response, False, False)
        js = response.json()
        hits = js['results'][0]['hits']
        out += [f"{_dict['title']}, https://www.footlocker.ae{_dict['url']}" for _dict in hits]

    # write data to file
    out = "\n".join(out)
    with open('out.txt', 'w', encoding='utf-8') as file:
        file.write(out)


def parser():
    with open('src.json') as file:
        js = load(file)

    print(len(js['results'][0]['hits']))
    hits = js['results'][0]['hits']
    for _dict in hits:
        # if _dict['is_buyable']:
        #     continue
        title = _dict['title']
        new_arrivals = datetime.utcfromtimestamp(
            int(_dict['changed'])
        ).strftime('%A, %B %d, %Y %H:%M:%S')
        # if int(_dict['stock_quantity']) != 1:
        #     continue

        # print(type(_dict['is_buyable']['en']))
        url = f"https://www.footlocker.ae{_dict['url']}"
        stock = _dict["stock_quantity"]
        _stock = _dict["stock"]
        # print(_dict)
        # print(_dict['is_new']['en'], _dict['is_buyable']['en'], stock, url)
        print(stock, _stock, new_arrivals, title, url)


send_req()
# parser()