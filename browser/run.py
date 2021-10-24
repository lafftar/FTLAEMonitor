import asyncio
from asyncio import sleep
from random import randint

from browser.base_browser import BasePlaywright
from browser.browser_handler import PlaywrightBrowserHandler


async def single_run():
    play = BasePlaywright()
    play.is_headless_browser = False
    play.viewport = {
        'width': randint(900, 1100),
        'height': randint(600, 1100)
    }
    await play.set_random_proxy()
    await play.launch_browser()
    await play.go_to('https://browserleaks.com/ip')
    await sleep(360)


async def multi_run():
    await asyncio.gather(*(single_run() for _ in range(2)))
    pbh: PlaywrightBrowserHandler = PlaywrightBrowserHandler.instance()
    await pbh.close_all_browsers()
    await pbh.stop_playwright()


if __name__ == "__main__":
    asyncio.run(multi_run())

# @todo
"""
- Make base mouse movement to selectors, mouse movement during load, minimal mouse jiggle during type, add noise.
"""