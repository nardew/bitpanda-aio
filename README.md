# bitpanda-aio 2.0.0

[![](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-365/) [![](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-374/)

`bitpanda-aio` is a Python library providing access to [Bitpanda Global Exchange API](https://developers.bitpanda.com/exchange/). Library implements bitpanda's REST API as well as websockets.

`bitpanda-aio` is designed as an asynchronous library utilizing modern features of Python and of supporting asynchronous libraries (mainly [async websockets](https://websockets.readthedocs.io/en/stable/) and [aiohttp](https://aiohttp.readthedocs.io/en/stable/)).

For changes see [CHANGELOG](https://github.com/nardew/bitpanda-aio/blob/master/CHANGELOG.md).

### Features
- access to complete Bitpanda's REST API (account details, market data, order management, ...) and websockets (account feed, market data feed, orderbook feed, ...)
- automatic connection management (reconnecting after remote termination, ...)
- channels bundled in one or multiple websockets processed in parallel 
- lean architecture setting ground for the future extensions and customizations
- fully asynchronous design aiming for the best performance

### Installation
```bash
pip install bitpanda-aio
```

### Prerequisites

Due to dependencies and Python features used by the library please make sure you use Python `3.6` or `3.7`.

Before starting using `bitpanda-aio`, it is necessary to take care of downloading your Bitpanda API key from your Bitpanda Global Exchange account

### Examples
#### REST API
```python
import asyncio
import logging
import datetime

from bitpanda.BitpandaClient import BitpandaClient
from bitpanda.Pair import Pair
from bitpanda.enums import OrderSide, TimeUnit

logger = logging.getLogger("bitpanda")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

async def run():
	api_key = "<YOUR_API_KEY>"

	client = BitpandaClient(api_key)

	print("Account balance:")
	await client.get_account_balances()

	print("Account fees:")
	await client.get_account_fees()

	print("Account orders:")
	await client.get_account_orders()

	print("Account order:")
	await client.get_account_order("1")

	print("Create market order:")
	await client.create_market_order(Pair("BTC", "EUR"), OrderSide.BUY, "1")

	print("Create limit order:")
	await client.create_limit_order(Pair("BTC", "EUR"), OrderSide.BUY, "10", "10")

	print("Create stop loss order:")
	await client.create_stop_limit_order(Pair("BTC", "EUR"), OrderSide.BUY, "10", "10", "10")

	print("Delete orders:")
	await client.delete_account_orders(Pair("BTC", "EUR"))

	print("Delete order:")
	await client.delete_account_order("1")

	print("Order trades:")
	await client.get_account_order_trades("1")

	print("Trades:")
	await client.get_account_trades()

	print("Trade:")
	await client.get_account_trade("1")

	print("Trading volume:")
	await client.get_account_trading_volume()

	print("Currencies:")
	await client.get_currencies()

	print("Candlesticks:")
	await client.get_candlesticks(Pair("BTC", "EUR"), TimeUnit.DAYS, "1", datetime.datetime.now() - datetime.timedelta(days=7), datetime.datetime.now())

	print("Fees:")
	await client.get_account_fees()

	print("Instruments:")
	await client.get_instruments()

	print("Order book:")
	await client.get_order_book(Pair("BTC", "EUR"))

	print("Time:")
	await client.get_time()

	await client.close()

if __name__ == "__main__":
	asyncio.run(run())
```

#### WEBSOCKETS
```python
import asyncio
import logging

from bitpanda.BitpandaClient import BitpandaClient
from bitpanda.Pair import Pair
from bitpanda.subscriptions import AccountSubscription, PricesSubscription, OrderbookSubscription, \
	CandlesticksSubscription, MarketTickerSubscription, CandlesticksSubscriptionParams
from bitpanda.enums import TimeUnit

logger = logging.getLogger("bitpanda")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

async def order_book_update(response : dict) -> None:
	print(f"Callback {order_book_update.__name__}: [{response}]")

async def run():
	api_key = "<YOUR_API_KEY>"

	client = BitpandaClient(api_key)

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

```

All examples can be found in `client-example/client.py` in the GitHub repository.

### Support

If you like the library and you feel like you want to support its further development, enhancements and bugfixing, then it will be of great help and most appreciated if you:
- file bugs, proposals, pull requests, ...
- spread the word
- donate an arbitrary tip
  * BTC: 15JUgVq3YFoPedEj5wgQgvkZRx5HQoKJC4
  * ETH: 0xf29304b6af5831030ba99aceb290a3a2129b993d
  * ADA: DdzFFzCqrhshyLV3wktXFvConETEr9mCfrMo9V3dYz4pz6yNq9PjJusfnn4kzWKQR91pWecEbKoHodPaJzgBHdV2AKeDSfR4sckrEk79
  * XRP: rhVWrjB9EGDeK4zuJ1x2KXSjjSpsDQSaU6 **+ tag** 599790141

### Contact

If you feel you want to get in touch, then please

- use Github Issues if it is related to the development, or
- send an e-mail to <img src="http://safemail.justlikeed.net/e/b5846997f972f029d244da6aa5998a74.png" border="0" align="absbottom">

### Affiliation

In case you are interested in an automated trading bot that will utilize `bitpanda-aio` in the near future, then feel free to visit my other project [creten](https://github.com/nardew/creten).
