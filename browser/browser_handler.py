import asyncio
from asyncio import sleep
from typing import Union
from playwright.async_api import async_playwright
from playwright.async_api import Browser, Playwright

from utils.base import Base
from utils.root import get_project_root
from utils.singleton import Singleton


@Singleton
class PlaywrightBrowserHandler(Base):
    def __init__(self):
        super().__init__()
        self.browser: Union[Browser, None] = None
        self.all_browsers: Union[list[Browser, ...], None] = []
        self.playwright: Union[Playwright, None] = None
        self.is_headless_browser: bool = True

        # ensuring no browser exceeds this num of contexts. really helps with memory.
        self.max_contexts_per_browser = 5

        # ensures the browsers launch one after the other. so we don't have a kinda race condition
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(1)

        # browser modes to launch
        self.is_firefox: bool = True
        self.is_chrome: bool = True

    def prnt_frmt(self, text):
        if not self.browser:
            browser_context_len = 'N/A'
        else:
            browser_context_len = len(self.browser.contexts)
        return f'\n' \
               f'\t[PLAYWRIGHT BROWSER HANDLER]\n' \
               f'\t[{len(self.all_browsers)} Total Browsers | {browser_context_len} Contexts for Current Browser]\n' \
               f'\t\t[Message]: {text}'

    async def _launch_firefox_browser(self):
        p = self.playwright.firefox
        self.browser = await p.launch(
            headless=self.is_headless_browser,
            firefox_user_prefs={
                'media.peerconnection.enabled': False,
                'javascript.options.mem.high_water_mark': 30,
                'javascript.options.mem.max': 102400
            }
        )

    async def _launch_chrome_browser(self):
        p = self.playwright.chromium
        self.browser = await p.launch(
            headless=self.is_headless_browser,
            proxy={'server': 'http://per-context'},
            args=[
                f"--disable-extensions-except={get_project_root()}/browser/chrome_extensions/WebRTC-Control_v0.2.9",
                f"--load-extension={get_project_root()}/browser/chrome_extensions/WebRTC-Control_v0.2.9",
            ],
            chromium_sandbox=True
        )

    async def launch_browser(self):
        # starting playwright if necessary
        if not self.playwright:
            self.playwright = await async_playwright().start()

        if self.is_firefox:
            await self._launch_firefox_browser()

        if self.is_chrome:
            await self._launch_chrome_browser()

        self.debug('New Browser Launched')

        # add browser to all current browsers
        self.all_browsers.append(self.browser)

    async def return_browser(self):
        async with self.semaphore:
            # no browser, first run, return
            if not self.browser:
                self.debug('Browser is None')
                await self.launch_browser()
                return self.browser

            # checks all browsers, closes browsers with 0 contexts
            for browser in self.all_browsers:
                if browser == self.browser:
                    continue
                if len(browser.contexts) == 0:
                    self.all_browsers.remove(browser)
                    await browser.close()
                    await sleep(0.1)
                    self.debug('Closed Browser with 0 Contexts')

            if len(self.browser.contexts) == self.max_contexts_per_browser:
                # if all browsers are at max contexts
                self.debug('Launching New Browser')
                await self.launch_browser()

            return self.browser

    async def return_context(self, **kwargs):
        async with self.semaphore:
            await sleep(0.001)
            context = await self.browser.new_context(**kwargs)
            self.debug('New Context Created.')
            return context

    async def close_browser(self):
        """
        Close current browser. Not sure when this will be needed quite yet.
        :return:
        """
        if self.browser:
            await self.browser.close()
            self.browser = None
        # should we be stopping playwright here?

    async def stop_playwright(self):
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def close_all_browsers(self):
        for browser in self.all_browsers:
            if browser:
                await browser.close()
        await self.close_browser()
        self.all_browsers = []
        self.info('All Browsers Closed')