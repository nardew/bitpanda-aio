import asyncio
import pathlib
import logging
import datetime
import os

from bitpanda.BitpandaClient import BitpandaClient
from bitpanda.Pair import Pair
from bitpanda.subscriptions import AccountSubscription, PricesSubscription, OrderbookSubscription, \
	CandlesticksSubscription, MarketTickerSubscription, CandlesticksSubscriptionParams
from bitpanda.enums import OrderSide, TimeUnit

LOG = logging.getLogger("bitpanda")
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())

print(f"Available loggers: {[name for name in logging.root.manager.loggerDict]}\n")

async def order_book_update(response : dict) -> None:
	print(f"Callback {order_book_update.__name__}: [{response}]")

async def run():
	print("STARTING BITPANDA CLIENT\n")

	# to generate a certificate use 'openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out certificate.pem'
	certificate_path = pathlib.Path(__file__).with_name("certificate.pem")

	# to retrieve your API key go to your bitpanda global exchange account and store it in BITPANDA_API_KEY environment
	# variable
	api_key = os.environ['BITPANDAAPIKEY']

	client = BitpandaClient(certificate_path, api_key)

	# REST api calls
	print("REST API")

	print("\nTime:")
	response = await client.get_time()
	print(f"Headers: {response['headers']}")
	
	print("\nAccount balance:")
	await client.get_account_balances()

	print("\nAccount fees:")
	await client.get_account_fees()

	print("\nAccount orders:")
	await client.get_account_orders()

	print("\nAccount order:")
	await client.get_account_order("1")

	print("\nCreate market order:")
	await client.create_market_order(Pair("BTC", "EUR"), OrderSide.BUY, "1")

	print("\nCreate limit order:")
	await client.create_limit_order(Pair("BTC", "EUR"), OrderSide.BUY, "10", "10")

	print("\nCreate stop loss order:")
	await client.create_stop_limit_order(Pair("BTC", "EUR"), OrderSide.BUY, "10", "10", "10")

	print("\nDelete orders:")
	await client.delete_account_orders(Pair("BTC", "EUR"))

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
	await client.get_candlesticks(Pair("BTC", "EUR"), TimeUnit.DAYS, "1", datetime.datetime.now() - datetime.timedelta(days=7), datetime.datetime.now())

	print("\nFees:")
	await client.get_account_fees()

	print("\nInstruments:")
	await client.get_instruments()

	print("\nOrder book:")
	await client.get_order_book(Pair("BTC", "EUR"))

	# Websockets
	print("\nWEBSOCKETS\n")

	# Bundle several subscriptions into a single websocket
	client.compose_subscriptions([
		AccountSubscription(),
		PricesSubscription([Pair("BTC", "EUR")]),
		OrderbookSubscription([Pair("BTC", "EUR")], "50", callbacks = [order_book_update]),
		CandlesticksSubscription([CandlesticksSubscriptionParams(Pair("BTC", "EUR"), TimeUnit.MINUTES, 1)]),
		MarketTickerSubscription([Pair("BTC", "EUR")])
	])

	# Bundle another subscriptions into a separate websocket
	client.compose_subscriptions([
		OrderbookSubscription([Pair("ETH", "EUR")], "50", callbacks = [order_book_update]),
	])

	# Execute all websockets asynchronously
	await client.start_subscriptions()

	await client.close()

if __name__ == "__main__":
	asyncio.run(run())
