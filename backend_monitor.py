import asyncio
from copy import deepcopy
from asyncio import sleep

import aiohttp
import httpx
from colorama import init

from utils.custom_logger import logger
from utils.global_vars import GLOBAL
from utils.tools import print_req_info, auth, update_title
from utils.webhook import send_webhook

init()


class AlgoliaStuff:
    def __init__(self):
        self.headers = {
            'Connection': 'keep-alive'
        }

        self.params = {
            'x-algolia-agent':
                'Algolia for JavaScript (3.35.1); Browser (lite); react (16.9.0); '
                'react-instantsearch (5.7.0); JS Helper (2.28.0)',
            'x-algolia-application-id': '3JYJSOXZO1',
            'x-algolia-api-key': '2da2a6f7496eed8347cd476da1a006b0'
        }

        not_filters = '(NOT field_category_name.lvl1: "Men\'s > Shoes") AND' \
                      '(NOT field_category_name.lvl1: "Women\'s > Shoes") AND' \
                      '(NOT field_category_name.lvl2: "Kids\' > 8+ Years > Shoes") AND' \
                      '(NOT field_category_name.lvl2: "Kids\' > 4 to 8 Years > Shoes") AND' \
                      '(NOT field_category_name.lvl2: "Kids\' > Upto 4 Years > Shoes")'

        filters = '(field_category_name.lvl1: "Men\'s > Shoes") OR' \
                  '(field_category_name.lvl1: "Women\'s > Shoes") OR' \
                  '(field_category_name.lvl2: "Kids\' > 8+ Years > Shoes") OR' \
                  '(field_category_name.lvl2: "Kids\' > 4 to 8 Years > Shoes") OR' \
                  '(field_category_name.lvl2: "Kids\' > Upto 4 Years > Shoes")'

        base_payload = {
            "requests": [
                {
                    "indexName": "01live_flae_en",
                    "params": 'query=shoes'
                              '&hitsPerPage=1000'
                              '&page=0'
                }
            ]
        }

        # page 0, filters
        self.payload_1 = deepcopy(base_payload)
        self.payload_1["requests"][0]["params"] += f'&filters={filters}'

        # page 1, filters
        self.payload_2 = deepcopy(base_payload)
        self.payload_2["requests"][0]["params"] = self.payload_2["requests"][0]["params"] \
            .replace('page=0', 'page=1')
        self.payload_2["requests"][0]["params"] += f'&filters={filters}'

        # page 0, no filters
        self.payload_3 = deepcopy(base_payload)
        self.payload_3["requests"][0]["params"] += f'&filters={not_filters}'

        # page 1, no filters
        self.payload_4 = deepcopy(base_payload)
        self.payload_4["requests"][0]["params"] = self.payload_4["requests"][0]["params"] \
            .replace('page=0', 'page=1')
        self.payload_4["requests"][0]["params"] += f'&filters={not_filters}'


class Hold:
    def __init__(self):
        self.num_results: int = 0
        self.old_results: dict = {}
        """
        self.old_results
        key: value
        url: {
                    'URL': url,
                    'TITLE': title,
                    'SKU': sku,
                    'PRICE': price
                }
        """


H = Hold()
Alg = AlgoliaStuff()


async def send_req(payload: dict, client: httpx.AsyncClient, current: dict):
    while True:
        try:
            response = await client.post(
                'https://3jyjsoxzo1.algolia.net/1/indexes/*/queries',
                headers=Alg.headers,
                params=Alg.params,
                json=payload
            )
            print_req_info(response, False, False)
            break
        except (httpx.ConnectTimeout, httpx.ProxyError, httpx.ConnectError,
                httpx.ReadError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError,
                httpx.ProxyError):
            logger().exception('Error')
            await sleep(2)

    # parse results
    js = response.json()
    hits = js['results'][0]['hits']
    for _dict in hits:
        url = f"https://www.footlocker.ae{_dict['url']}"
        title = _dict['title']
        price = _dict['final_price']
        sku = _dict['sku']
        stock = _dict['stock_quantity']
        try:
            image_url = _dict['media'][1]['url']
        except IndexError:
            image_url = _dict['media'][0]['url']
        current[url] = {
            'URL': url,
            'TITLE': title,
            'SKU': sku,
            'PRICE': price,
            'IMAGE_LINK': image_url,
            'STOCK_QUANTITY': stock
        }


async def send_webhooks(_dict: dict, message: str = 'NO_REPEAT'):
    client = aiohttp.ClientSession()
    try:
        await asyncio.gather(*
                             (send_webhook(_dict=_dict,
                                           url=url,
                                           webhook_client=client,
                                           message=message)
                              for url in GLOBAL.webhooks
                              )
                             )
    finally:
        await client.close()


async def check():
    current = dict()
    client = httpx.AsyncClient()
    # get data from both pages
    try:
        await asyncio.gather(send_req(Alg.payload_1, client, current),
                             send_req(Alg.payload_2, client, current),
                             send_req(Alg.payload_3, client, current),
                             send_req(Alg.payload_4, client, current))
    finally:
        await client.aclose()

    if H.old_results:
        current_urls = set(current.keys())
        old_urls = set(H.old_results.keys())

        """
        current - old = new item
        old - current = item pulled
        """

        new_items = current_urls - old_urls
        pulled_items = old_urls - current_urls

        if new_items:
            logger().info(f'{len(new_items)} new items found!')
            await asyncio.gather(*
                                 (
                                     send_webhooks(_dict=current[url], message='NO_REPEAT')
                                     for url in new_items
                                 )
                                 )

        if pulled_items:
            logger().info(f'{len(pulled_items)} pulled items found!')
            await asyncio.gather(*
                                 (
                                     send_webhooks(_dict=H.old_results[url], message='PULLED')
                                     for url in pulled_items
                                 )
                                 )

    H.old_results = current
    logger().debug(f'Checked. {len(H.old_results)} shoes loaded on backend.')
    return


async def check_auth():
    while True:
        auth()
        await sleep(60)


async def check_forever():
    while True:
        await check()
        await sleep(30)


async def run():
    try:
        await asyncio.gather(check_auth(), check_forever())
    except Exception:
        logger().exception('Please contact @winwinwinwin#0001 on discord.')
        input()


if __name__ == "__main__":
    update_title('Running.')
    asyncio.run(run())
