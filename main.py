import os
import logging
import json
import asyncio
from aiohttp import ClientSession
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask, request, jsonify

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger()

TOKEN = os.environ.get("TOKEN")

urls = [
    "https://api.binance.us/api/v3/ticker/price?symbol=BTCUSDT",
    "https://api.binance.us/api/v3/ticker/price?symbol=ETHBTC",
    "https://api.binance.us/api/v3/ticker/price?symbol=DOTUSDT",
    "https://api.binance.us/api/v3/ticker/price?symbol=ETHUSDT"
    ]


logger = logging.getLogger()

with open('config.json', 'r') as f:
    data = json.load(f)

#fetch pricese from binance asynchronously
async def fetch_url(session, url):
    response = await session.get(url)
    return await response.json()


# comparing values from config file with fresh prices
def price_comparison(price, config):
    coins_dict_comparison_done = {}
    for i, (coin, coin_property) in enumerate(zip(price, config.values())):
        if 'more_eq' in coin_property['trigger']:
            if coin['price'] >= coin_property['price']:
                coins_dict_comparison_done[coin['symbol']] = 'Alert! ETH/BTC ratio is below {} threshold!'.format(coin_property['price'])
        elif 'more' in coin_property['trigger']:
            if coin['price'] > coin_property['price']:
                coins_dict_comparison_done[coin['symbol']] = 'Alert! BTC is more than ${}'.format(coin_property['price'])
        elif 'less_eq' in coin_property['trigger']:
            if coin['price'] <= coin_property['price']:
                coins_dict_comparison_done[coin['symbol']] = 'Alert! ETH is below ${}!'.format(coin_property['price'])
        elif 'less' in coin_property['trigger']:
            if coin['price'] < coin_property['price']:
                coins_dict_comparison_done[coin['symbol']] = 'Alert! ETH/BTC ratio is below {} threshold!'.format(coin_property['price'])
    return coins_dict_comparison_done

async def start_handler(update: Updater, context: CallbackContext):
    update.message.reply_text("Hello! Use /signals command to get a crypto alerts!")

async def get_signals(update: Updater, context: CallbackContext):
    async with ClientSession() as session:
            tasks = []
            for url in urls:
                task = asyncio.create_task(fetch_url(session, url))
                tasks.append(task)
            prices = await asyncio.gather(*tasks)
            compare = price_comparison(prices, data)
    for value in compare.values():
        update.message.reply_text('{}'.format(value))

def run(updater):
    PORT = os.environ.get('PORT', 8443)
    HEROKU_APP_NAME = os.environ.get('HEROKU_APP_NAME')
    updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN,
                              webhook_url="https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN)
                              )

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(CommandHandler("start", start_handler, run_async=True))
    updater.dispatcher.add_handler(CommandHandler("signals", get_signals, run_async=True))
    run(updater)