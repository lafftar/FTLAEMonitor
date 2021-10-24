from asyncio import sleep

from discord import Colour, Embed, AsyncWebhookAdapter, Webhook


async def send_webhook(caller, url, webhook_client, message='NO_REPEAT'):
    # sending webhook
    webhook = Webhook.from_url(
        url=url,
        adapter=AsyncWebhookAdapter(caller.webhook_client))

    # create embed
    title = 'Product Live!'
    color = Colour.green()
    if message == 'REPEAT':
        title = 'Product Live! (Reminder)'
        color = Colour.dark_green()
    elif message == 'PULLED':
        title = 'Product Pulled!'
        color = Colour.dark_orange()

    embed = Embed(title=caller.product_name, color=color, url=caller.link)
    embed.set_footer(text='WINX4 Bots - winwinwinwin#0001',
                     icon_url='https://images6.alphacoders.com/909/thumb-1920-909641.png')
    embed.set_thumbnail(url=caller.image_link)
    embed.add_field(name='Status', value=title, inline=False)
    embed.add_field(name='Price', value=f'{caller.price}', inline=False)
    embed.add_field(name='SKU', value=f'{caller.sku}', inline=False)

    while True:
        try:
            await webhook.send(username='FTL.AE Monitor',
                               avatar_url=
                               'https://d1yjjnpx0p53s8.cloudfront.net/styles/logo-thumbnail/s3/'
                               '0002/5414/brand.gif?itok=c0LjV97s',
                               embed=embed,
                               )
            caller.info('Sent Webhook')
            break
        except Exception:
            caller.exception('Webhook Failed')
            await sleep(2)
