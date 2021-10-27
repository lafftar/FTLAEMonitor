import asyncio
from asyncio import sleep
from discord import Colour, Embed, AsyncWebhookAdapter, Webhook

from utils.custom_logger import logger


async def send_webhook(_dict, url, webhook_client, message='NO_REPEAT'):
    product_name = _dict['TITLE']
    link = _dict['URL']
    image_link = _dict['IMAGE_LINK']
    price = _dict['PRICE']
    sku = _dict['SKU']
    stock = _dict['STOCK_QUANTITY']

    # sending webhook
    webhook = Webhook.from_url(
        url=url,
        adapter=AsyncWebhookAdapter(webhook_client))

    # create embed
    title = 'Product Live!'
    color = Colour.green()
    if message == 'REPEAT':
        title = 'Product Live! (Reminder)'
        color = Colour.dark_green()
    elif message == 'PULLED':
        title = 'Product Pulled!'
        color = Colour.dark_orange()

    embed = Embed(title=product_name, color=color, url=link)
    embed.set_footer(text='WINX4 Bots - winwinwinwin#0001',
                     icon_url='https://images6.alphacoders.com/909/thumb-1920-909641.png')
    embed.set_thumbnail(url=image_link)
    embed.add_field(name='Status', value=title, inline=False)
    embed.add_field(name='Price', value=f'{price}', inline=False)
    embed.add_field(name='Stock', value=f'{stock}', inline=False)
    embed.add_field(name='SKU', value=f'{sku}', inline=False)

    while True:
        try:
            await webhook.send(username='FTL.AE Monitor',
                               avatar_url=
                               'https://d1yjjnpx0p53s8.cloudfront.net/styles/logo-thumbnail/s3/'
                               '0002/5414/brand.gif?itok=c0LjV97s',
                               embed=embed,
                               )
            logger().info('Sent Webhook')
            break
        except Exception:
            logger().exception('Webhook Failed')
            await sleep(2)


if __name__ == "__main__":
    import aiohttp
    from utils.global_vars import GLOBAL


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

    asyncio.run(send_webhooks(_dict={
                'URL': f"https://www.footlocker.ae/en/buy-jordan-break-grade-school-slides-black-white.html",
                'TITLE': "Jordan Break - Grade School Slides",
                'SKU': 'LF316701081404',
                'PRICE': '600',
                'IMAGE_LINK': 'https://www.footlocker.ae/sites/g/files/bndsjb891/files/styles/product_listing/public/media/als-ecom-pimsfl-prod-s3/assets/FootLocker/316701081404_02.1199041.jpg?itok=fHpznLe_',
        'STOCK_QUANTITY': '20'
            }))