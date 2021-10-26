import asyncio
import functools
import sys
from asyncio import sleep
from json import dumps, JSONDecodeError
from os import system
from time import sleep as sync_sleep
from typing import Union

import aiohttp
import httpcore
import httpx
from aiohttp import client_exceptions
from colorama import init, Fore
from faker import Faker

from utils.root import get_project_root
from utils.global_vars import GLOBAL

init()
system("cls")
FIRST_PRINT = False
FAKE = Faker()


def print_req_info(res: httpx.Response, print_headers: bool = False, print_body: bool = False):
    if not res:
        print('No Response Body')
        return

    with open(f'{get_project_root()}/src.html', mode='w', encoding='utf-8') as file:
        try:
            with open(f'{get_project_root()}/src.json', mode='w', encoding='utf-8') as file:
                file.write(dumps(res.json(), indent=4))
                print('wrote json')
        except JSONDecodeError:
            file.write(res.text)
    if not print_headers:
        return

    req_str = f'{res.request.method} {res.request.url} {res.http_version}\n'
    for key, val in res.request.headers.items():
        req_str += f'{key}: {val}\n'
    res.read()
    res.request.read()
    if res.request.content:
        try:
            req_str += f'Req Body: {dumps(res.request.read().decode(), indent=4)}'
        except JSONDecodeError:
            req_str += f'Req Body: {res.request.content}'
    req_str += '\n'

    resp_str = f'{res.http_version} {res.status_code} {res.reason_phrase}\n'
    for key, val in res.headers.items():
        resp_str += f'{key}: {val}\n'
    resp_str += f'Cookie: '
    for key, val in res.cookies.items():
        resp_str += f'{key}={val};'
    resp_str += '\n'
    if print_body:
        resp_str += f"Resp Body: {res.text}"
    resp_str += '\n|\n|'

    sep_ = '-' * 10
    boundary = '|'
    boundary += '=' * 100
    print(boundary)
    print(f'|{sep_}REQUEST{sep_}')
    print(req_str)
    print(f'|{sep_}RESPONSE{sep_}')
    print(resp_str)
    print(f'|History: {res.history}')
    for resp in res.history:
        print(resp.url, end=',')
    print()
    print(boundary)


async def send_req(req_obj: functools.partial, num_tries: int = 1) -> \
        Union[httpx.Response, aiohttp.ClientResponse, None]:
    """
    Central Request Handler. All requests should go through this.
    :param req_obj:
    :return:
    """
    for _ in range(num_tries):
        try:
            item = await req_obj()
            return item
        except (httpx.ConnectTimeout, httpx.ProxyError, httpx.ConnectError,
                httpx.ReadError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError,
                httpx.ProxyError,

                # aiohttp errors
                asyncio.exceptions.TimeoutError, client_exceptions.ClientHttpProxyError,
                client_exceptions.ClientProxyConnectionError,
                client_exceptions.ClientOSError,
                client_exceptions.ServerDisconnectedError
                ):
            await sleep(1)
    return


def update_title(terminal_title):
    bot_name = 'FTL.AE Monitor'
    if sys.platform == 'linux':
        print(f'\33]0;[{bot_name}] | {terminal_title}\a', end='', flush=True)
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(f'[{bot_name}] | {terminal_title}')


def check_license(license_key):
    headers = {
        'Authorization': f'Bearer pk_sKa7BLS6lRcuUPUDvtSMCXRjxs7KV7bW'
    }

    req = httpx.get(f'https://api.hyper.co/v4/licenses/{license_key}',
                    headers=headers,
                    verify=True)
    if req.status_code == 200:
        return req.json()

    return


def auth():
    global FIRST_PRINT
    license_data = check_license(GLOBAL.key)

    if not license_data:
        print(f'{Fore.LIGHTRED_EX}Your key is not valid. '
              f'Please check again or contact winwinwinwin#0001.\n'
              f'Your key - {GLOBAL.key}')
        sync_sleep(10)
        raise KeyboardInterrupt
    name = license_data['metadata']['Name']
    if not FIRST_PRINT:
        print(f'\n\n{Fore.LIGHTBLUE_EX}Hello {name}. Your key is valid. You are allowed unlimited instances.\n\n')
        FIRST_PRINT = True
