"""
Use playwright chrome browser to gen cloudflare cookies.
Pass it to httpx and go crazy.

SKU can be grabbed from link.
    On the ATC btn.
    Base 64 encoded sku.

Proxy apparently does not need to stay the same as cookie.

Grab CF cookies from browser, or use manual gotten cookies.
Go to urls in file
webhook if item is found
"""
import asyncio
import functools
from asyncio import sleep
from random import randint, choice
from time import time
from typing import Union

import aiohttp
import ray as ray
from bs4 import BeautifulSoup

import httpx
from ray.thirdparty_files import psutil

from utils.base import Base
from utils.global_vars import GLOBAL
from utils.tools import print_req_info, update_title, auth, send_req
from utils.webhook import send_webhook


REQ_COUNTER = set()
REQ_COUNTER_SEM = asyncio.Semaphore(1)
CURRENT_PROXIES = []
SENT_WEBHOOKS = {}


async def update_timer():
    # add to req_counter. update title
    REQ_COUNTER.add(time())
    for _time in REQ_COUNTER.copy():
        if time() - _time > 1:
            REQ_COUNTER.discard(_time)
        update_title(f'Checks in Last (1) Second: [{len(REQ_COUNTER)}]')
    return


def is_available(res: httpx.Response):
    if res.text.find('"availability": "http://schema.org/InStock"') != -1:
        return True


class FTLAEMonitor(Base):
    def __init__(self, link, webhook_client, webhook_sem):
        super().__init__()
        self.counter.tasks += 1
        self.task_num = self.counter.tasks

        self.link: str = link
        self.webhook_client = webhook_client
        self.webhook_sem = webhook_sem
        self.headers: dict = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
        }

        self.price, self.product_name, self.image_link, self.resp, self.sku = (None for _ in range(5))
        self.client: Union[httpx.AsyncClient, None] = None
        self.cf_cookie: Union[str, None] = None

    async def create_client(self):
        if not self.client:
            self.client = httpx.AsyncClient(proxies=choice(GLOBAL.isps))
            # self.client.cookies.set(name='cf_clearance', value='dzLUHkun0DVyOijQXA1q8bvWHtQ5714lEr4CDPofgzc')

    async def close_client(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def set_product(self):
        src = BeautifulSoup(self.resp.text, 'lxml')
        src = src.select('script[type="application/ld+json"]')
        src = eval(src[1].string)
        self.product_name = src['name']
        self.image_link = src['image']
        self.sku = src['sku']
        self.price = f"{src['offers']['price']} {src['offers']['priceCurrency']}"

    async def check_page(self):
        req = httpx.Request(
            method='GET',
            url=self.link,
            headers=self.headers,
            cookies=self.client.cookies
        )
        self.resp = await send_req(functools.partial(self.client.send, req))
        if not self.resp:
            self.warn('No Resp')
            return

        results = await asyncio.gather(*(self.is_available(), update_timer()))

        self.debug(f'Checked - {self.resp.status_code}')

        if any(results):
            return True

    async def is_available(self):
        if not is_available(self.resp):
            # if not available and was previously pushed.
            async with self.webhook_sem:
                if SENT_WEBHOOKS.get(self.sku, None):
                    self.debug('Product has been pulled!')
                    await self.send_webhooks('PULLED')
                    SENT_WEBHOOKS.pop(self.sku)
                    return True
            return

        await self.set_product()

        async with self.webhook_sem:
            if not SENT_WEBHOOKS.get(self.sku, None):
                self.debug('New Webhook! Sending Now!')
                await self.send_webhooks('NO_REPEAT')
                SENT_WEBHOOKS[self.sku] = time()

            if SENT_WEBHOOKS.get(self.sku, None):
                if time() - SENT_WEBHOOKS[self.sku] < GLOBAL.reminder_timeout:
                    self.debug('Already Sent Webhook Within Timeout Period')
                    return
                if time() - SENT_WEBHOOKS[self.sku] > GLOBAL.reminder_timeout:
                    self.debug('Already Sent Webhook. But Timeout period has been exceeded.')
                    await self.send_webhooks('REPEAT')
                    SENT_WEBHOOKS[self.sku] = time()
                    return

    async def send_webhooks(self, message):
        await asyncio.gather(*(send_webhook(caller=self,
                                            url=link,
                                            message=message)
                               for link in GLOBAL.webhooks))

    async def run(self):
        await self.create_client()
        while True:
            if not await self.check_page():
                continue
            await self.is_available()
            break
        await self.close_client()


# @todo - need to make sure only one of these run at a time

async def check_auth():
    # print('Inside _check_auth()')
    while True:
        auth()
        await sleep(60)


# @ray.remote(num_cpus=1)
# def check_auth():
#     print('Inside check_auth()')
#     asyncio.run(_check_auth())


# num_cpus = psutil.cpu_count(logical=True)


# @ray.remote(num_cpus=num_cpus)
# class AsyncActor:
async def run():
    print('Inside AsyncActor')
    webhook_client = aiohttp.ClientSession()
    webhook_sem = asyncio.Semaphore(1)
    tasks = [
                 FTLAEMonitor(
                     link,
                     webhook_client=webhook_client,
                     webhook_sem=webhook_sem
                 ).run()
                 for link in GLOBAL.links
             ]
    try:
        await asyncio.gather(*tasks, check_auth())
    finally:
        await webhook_client.close()


if __name__ == "__main__":
    asyncio.run(run())
