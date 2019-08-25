import asyncio
import pathlib
import logging
import datetime
import os

from bitpanda.BitpandaClient import BitpandaClient
from bitpanda.Pair import Pair
from bitpanda.websockets import CandlesticksSubscriptionParams
from bitpanda.enums import OrderSide

logger = logging.getLogger("bitpanda")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

print(f"Available loggers: {[name for name in logging.root.manager.loggerDict]}\n")

async def run():
	print("STARTING BITPANDA CLIENT\n")

	# to generate a certificate use 'openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out certificate.pem'
	certificate_path = pathlib.Path(__file__).with_name("certificate.pem")

	# to retrieve your API key go to your bitpanda global exchange account and store it in BITPANDA_API_KEY environment
	# variable
	api_key = os.environ['BITPANDA_API_KEY']

	client = BitpandaClient(certificate_path, api_key)

	# REST api calls
	print("REST API")
	print("\nAccount balance:")
	await client.get_account_balances()

	print("\nAccount fees:")
	await client.get_account_fees()

	print("\nAccount orders:")
	await client.get_account_orders()

	print("\nAccount order:")
	await client.get_account_order("1")

	print("\nCreate market order:")
	await client.create_account_order_market("BTC", "EUR", OrderSide.BUY, "1")

	print("\nCreate limit order:")
	await client.create_account_order_limit("BTC", "EUR", OrderSide.BUY, "10", "10")

	print("\nCreate stop loss order:")
	await client.create_account_order_stop_limit("BTC", "EUR", OrderSide.BUY, "10", "10", "10")

	print("\nDelete orders:")
	await client.delete_account_orders("BTC", "EUR")

	print("\nDelete order:")
	await client.delete_account_order("1")

	print("\nOrder trades:")
	await client.get_account_order_trades("1")

	print("\nTrades:")
	await client.get_account_trades()

	print("\nTrade:")
	await client.get_account_trade("1")

	print("\nTrading volume:")
	await client.get_account_trading_volume()

	print("\nCurrencies:")
	await client.get_currencies()

	print("\nCandlesticks:")
	await client.get_candlesticks("BTC", "EUR", "DAYS", "1", datetime.datetime.now() - datetime.timedelta(days=7), datetime.datetime.now())

	print("\nFees:")
	await client.get_account_fees()

	print("\nInstruments:")
	await client.get_instruments()

	print("\nOrder book:")
	await client.get_order_book("BTC", "EUR")

	print("\nTime:")
	await client.get_time()

	# Websockets
	print("\nWEBSOCKETS\n")
	client.subscribe_prices_ws([Pair("BTC", "EUR")])
	client.subscribe_order_book_ws([Pair("BTC", "EUR")], 50)
	client.subscribe_account_ws()
	client.subscribe_candlesticks_ws([CandlesticksSubscriptionParams(Pair("BTC", "EUR"), "MINUTES", 1)])
	client.subscribe_market_ticker_ws([Pair("BTC", "EUR")])

	await client.start_websockets()

	await client.close()

if __name__ == "__main__":
	asyncio.run(run())
