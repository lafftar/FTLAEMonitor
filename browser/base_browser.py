import asyncio
from asyncio import sleep
from random import randint, uniform, choice
from typing import Union, Literal
from playwright import async_api
from playwright.async_api import ElementHandle
import playwright.async_api
from playwright.async_api import Browser, Page, Playwright, BrowserContext
from browser.browser_handler import PlaywrightBrowserHandler
from utils.base import Base
from utils.global_vars import GLOBAL
from utils.tools import FAKE


class BasePlaywright(Base):
    def __init__(self):
        # will be instantiated and modified during class life
        super().__init__()
        self.browser_handler: PlaywrightBrowserHandler = PlaywrightBrowserHandler.instance()
        self.playwright: Union[Playwright, None] = None
        self.browser: Union[Browser, None] = None
        self.page: Union[Page, None] = None
        self.is_headless_browser: bool = True
        self.viewport: Union[None, dict] = None
        self.proxy: Union[str, None] = None
        self.context: Union[BrowserContext, None] = None
        self.storage_state: Union[dict, None] = None
        self.img: Union[str, None] = None

    def prnt_frmt(self, text):
        return f'[BASE PLAYWRIGHT] ' \
               f': {text}'

    async def human_type(self,
                         selector: str = '[id="AdTitleForm"]',
                         element: ElementHandle = None,
                         text: str = 'Affordable Painting Services',
                         sleep_end: float = 0.01):
        if not element:
            element = await self.page.query_selector(selector)
        element_coords = await element.bounding_box()
        random_spot_inside_element = {
            'x': (element_coords['x'] + element_coords['width']) / uniform(1, 10),
            'y': (element_coords['y'] + element_coords['height']) / uniform(1, 10)
        }
        await element.scroll_into_view_if_needed()
        await self.page.mouse.move(x=random_spot_inside_element['x'],
                                   y=random_spot_inside_element['y'],
                                   steps=randint(5, 30))
        await element.click()
        for char in text:
            await self.page.keyboard.type(text=char)
            await sleep(uniform(0, sleep_end))

    async def set_random_proxy(self):
        self.proxy = choice(GLOBAL.isps)
        self.debug(f'Set Random Proxy\n'
                   f'\t\t[{self.proxy}]')

    async def check_if_selector_on_page(self, selector, timeout: float = 500):
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except playwright.async_api.TimeoutError:
            return False

    async def go_to(self,
                    url: str = 'http://kijiji.ca',
                    wait_until: Union[str, bool] = None,
                    referer: Union[str, bool] = None,
                    timeout: int = 5,
                    selector_timeout: int = 10,
                    selector_on_trgt_page: str = None,
                    retry_num: int = 2):
        """

        :param selector_on_trgt_page:
        :param url:
        :param wait_until:
        :param referer:
        :param timeout: in seconds, 1 is 1 second. Not 1 ms.
        :return:
        """
        for _ in range(retry_num):
            try:
                self.debug(f'Going to {url}')
                timeout = int(timeout * 1000)
                await self.page.goto(url,
                                     referer=referer,
                                     wait_until=wait_until,
                                     timeout=timeout)
                if selector_on_trgt_page:
                    if await self.wait_for_selector(selector=selector_on_trgt_page, timeout=selector_timeout):
                        self.debug('Page loaded successfully!')
                    else:
                        self.warn('Page not loaded successfully :(')
                        return False
                return True
            except playwright.async_api.TimeoutError:
                continue
            except playwright.async_api.Error as err:
                self.error(f'Either proxy or connection refused error - {err}')
                await self.page.reload()

    async def close_browser(self):
        if self.context:
            self.debug('About to close context')
            await self.context.close()
            self.context = None
            self.debug('Browser (Context) Closed. Remember to close the browser/stop playwright.')

    async def launch_browser(self, firefox: bool = True, chrome: bool = False):
        # make sure you're not launching two types of browsers in the same process
        if chrome:
            firefox = False
        if firefox:
            chrome = False

        # creating context/page settings
        if not self.viewport:
            self.viewport = {
                'width': randint(600, 700),
                'height': randint(600, 1100)
            }

        proxy = await self._return_formatted_proxy()
        latlng = FAKE.local_latlng(country_code='CA')
        latitude, longitude, city, timezone = latlng[0], latlng[1], latlng[2], latlng[-1]
        latitude, longitude = float(latitude), float(longitude)
        color_schemes = ["dark", "light", "no-preference", None]
        color_scheme = color_schemes[randint(0, len(color_schemes) - 1)]
        accuracies = [10 * num for num in range(20)]
        accuracy = accuracies[randint(0, len(accuracies) - 1)]

        # getting main browser instance
        self.browser_handler.is_headless_browser = self.is_headless_browser
        self.browser_handler.is_firefox = firefox
        self.browser_handler.is_chrome = chrome
        self.browser = await self.browser_handler.return_browser()
        context_args = {'viewport': self.viewport,
                        'timezone_id': timezone,
                        'proxy': {
                            'server': proxy['Proxy IP'],
                            'username': proxy['Proxy User'],
                            'password': proxy['Proxy Passwd']
                        },
                        'geolocation': {
                            'latitude': latitude,
                            'longitude': longitude,
                            'accuracy': accuracy
                        },
                        'permissions': ['geolocation'],
                        'color_scheme': color_scheme,
                        'storage_state': self.storage_state,
                        # record_har_path:f'{get_project_root()}/google_form/recordings/har',
                        }
        self.context = await self.browser_handler.return_context(**context_args)
        self.page = await self.context.new_page()

    async def _return_formatted_proxy(self) -> dict:
        proxy = self.proxy.split(':')
        if len(proxy) == 2:
            proxy_ip, proxy_user, proxy_passwd = self.proxy, 'None', 'None'
        else:
            proxy_ip, proxy_user, proxy_passwd = ('None' for _ in range(3))
            proxy_ip = f'{proxy[0]}:{proxy[1]}:{proxy[2]}'
            if len(proxy) > 3:
                proxy_user = f'{proxy[-2]}'
                proxy_passwd = f'{proxy[-1]}'

        proxy = {
            'Proxy IP': proxy_ip,
            'Proxy User': proxy_user,
            'Proxy Passwd': proxy_passwd
        }
        return proxy

    async def wait_for_selector(self, selector, timeout: float = 3,
                                suppress: bool = True,
                                state: Literal["attached", "detached", "hidden", "visible"] = 'visible'):
        """
        This suppresses the timeout error. Be careful.
        :param state:
        :param suppress:
        :param selector:
        :param timeout: in seconds. 0.5s.
        :return:
        """
        timeout = int(timeout * 1000)
        try:
            return await self.page.wait_for_selector(selector=selector, timeout=timeout, state=state)
        except async_api.TimeoutError:
            if suppress:
                return None
            raise async_api.TimeoutError(f'TimeoutError waiting for `{selector}`')


if __name__ == "__main__":
    pass
