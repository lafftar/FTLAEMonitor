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
from random import randint, choice
from typing import Union

import aiohttp
from bs4 import BeautifulSoup

import httpx

from utils.base import Base
from utils.global_vars import GLOBAL
from utils.tools import print_req_info
from utils.webhook import send_webhook


def is_available(res: httpx.Response):
    if res.text.find('"availability": "http://schema.org/InStock"') != -1:
        return True


class FTLAEMonitor(Base):
    def __init__(self, link, webhook_client):
        super().__init__()
        self.link: str = link
        self.webhook_client = webhook_client
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
        self.resp = await self.client.send(req)
        if not self.resp:
            self.warn('No Resp')
            return
        self.debug(f'Checked - {self.resp.status_code}')
        return True

    async def check_is_available(self):
        if not is_available(self.resp):
            return
        print_req_info(self.resp, True)
        await self.set_product()
        await self.send_webhook()

    async def send_webhook(self):
        await asyncio.gather(*(send_webhook(caller=self,
                                            url=link,
                                            webhook_client=self.webhook_client) for link in GLOBAL.webhooks))

    async def run(self):
        await self.create_client()
        while True:
            if not await self.check_page():
                continue
            await self.check_is_available()
            break
        await self.close_client()


async def run():
    webhook_client = aiohttp.ClientSession()
    await asyncio.gather(*
                         (FTLAEMonitor(link, webhook_client=webhook_client).run() for link in GLOBAL.links)
                         )
    await webhook_client.close()


if __name__ == "__main__":
    asyncio.run(run())
