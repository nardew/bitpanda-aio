import websockets
import json
import logging
import asyncio
from abc import ABC, abstractmethod

from bitpanda.Pair import Pair
from bitpanda import enums

logger = logging.getLogger(__name__)

class Websocket(ABC):
	WEB_SOCKET_URI = "wss://streams.exchange.bitpanda.com"

	def __init__(self, callbacks = None, ssl_context = None):
		self.callbacks = callbacks
		self.ssl_context = ssl_context

	async def run(self):
		try:
			# main loop ensuring proper reconnection after a graceful connection termination by the remote server
			while True:
				logger.debug(f"[{self.get_websocket_id()}] Initiating connection.")
				async with websockets.connect(Websocket.WEB_SOCKET_URI, ssl = self.ssl_context) as websocket:
					subscription_message = self.get_subscription_message()
					logger.debug(f"> [{self.get_websocket_id()}]: {subscription_message}")
					await websocket.send(json.dumps(subscription_message))

					# process subscription
					try:
						response = json.loads(await websocket.recv())
						logger.debug(f"< [{self.get_websocket_id()}]: {response}")
						if response['type'] == "SUBSCRIPTIONS":
							logger.info(f"< [{self.get_websocket_id()}]: Subscription performed properly for channels [" + ",".join([channel["name"] for channel in response["channels"]]) + "]")
						elif response['type'] == "ERROR":
							raise Exception(f"[{self.get_websocket_id()}] Request [{json.dumps(subscription_message)}] Response [{json.dumps(response)}]")
					except asyncio.CancelledError:
						raise
					except:
						logger.exception(f"[{self.get_websocket_id()}]: Error while performing subscription to websocket.")
						raise

					# start processing regular incoming messages
					while True:
						response = json.loads(await websocket.recv())
						logger.debug(f"< [{self.get_websocket_id()}]: {response}")

						if response["type"] == "CONNECTION_CLOSING":
							logger.warning(f"[{self.get_websocket_id()}]: Server is performing connection termination with an opportunity to reconnect.")
							break
						elif response["type"] == "HEARTBEAT":
							pass
						else:
							await self.process(response)
		except asyncio.CancelledError:
			logger.warning(f"[{self.get_websocket_id()}]: Websocket requested to be shutdown.")
		except Exception:
			logger.error(f"[{self.get_websocket_id()}] Exception occurred. Websocket will be closed.")
			raise

	async def process_callbacks(self, response):
		if self.callbacks is not None:
			await asyncio.gather(*[asyncio.create_task(cb(response)) for cb in self.callbacks])

	async def process(self, response):
		await self.process_callbacks(response)

	@abstractmethod
	def get_subscription_message(self):
		pass

	@abstractmethod
	def get_websocket_id(self):
		pass

	@staticmethod
	def _get_subscription_instrument_codes(pairs):
		return [pair.base + "_" + pair.quote for pair in pairs]

class AccountWebsocket(Websocket):
	def __init__(self, api_key, callbacks = None, ssl_context = None):
		super().__init__(callbacks, ssl_context)

		self.api_key = api_key

	def get_websocket_id(self):
		return "AccountWS"

	def get_subscription_message(self):
		return {
			"type": "SUBSCRIBE",
			"channels": [
				{
					"name": "ACCOUNT_HISTORY",
					"api_token": self.api_key
				}
			]
		}

class PriceWebsocket(Websocket):
	def __init__(self, pairs, callbacks = None, ssl_context = None):
		super().__init__(callbacks, ssl_context)

		self.pairs = pairs

	def get_websocket_id(self):
		return "PricesWS"

	def get_subscription_message(self):
		return {
			"type": "SUBSCRIBE",
			"channels": [
				{
					"name": "PRICE_TICKS",
					"instrument_codes": Websocket._get_subscription_instrument_codes(self.pairs)
				}
			]
		}

class OrderbookWebsocket(Websocket):
	def __init__(self, pairs, depth, callbacks = None, ssl_context = None):
		super().__init__(callbacks, ssl_context)

		self.pairs = pairs
		self.depth = depth

	def get_websocket_id(self):
		return "OrderbookWS"

	def get_subscription_message(self):
		return {
			"type": "SUBSCRIBE",
			"channels": [
				{
					"name": "ORDER_BOOK",
					"depth": self.depth,
					"instrument_codes": Websocket._get_subscription_instrument_codes(self.pairs)
				}
			]
		}

class CandlesticksSubscriptionParams(object):
	def __init__(self, pair : Pair, unit : enums.TimeUnit, period):
		self.pair = pair
		self.unit = unit
		self.period = period

class CandlesticksWebsocket(Websocket):
	def __init__(self, subscription_params, callbacks = None, ssl_context = None):
		super().__init__(callbacks, ssl_context)

		self.subscription_params = subscription_params

	def get_websocket_id(self):
		return "CandlesticksWS"

	def get_subscription_message(self):
		return {
			"type": "SUBSCRIBE",
			"channels": [
				{
					"name": "CANDLESTICKS",
					"properties": [{
						"instrument_code": params.pair.base + "_" + params.pair.quote,
						"time_granularity": {
							"unit": params.unit.value,
							"period": params.period
						}
					} for params in self.subscription_params]
				}
			]
		}

class MarketTickerWebsocket(Websocket):
	def __init__(self, pairs, callbacks = None, ssl_context = None):
		super().__init__(callbacks, ssl_context)

		self.pairs = pairs

	def get_websocket_id(self):
		return "MarketTickerWS"

	def get_subscription_message(self):
		return {
			"type": "SUBSCRIBE",
			"channels": [
				{
					"name": "MARKET_TICKER",
					"instrument_codes": Websocket._get_subscription_instrument_codes(self.pairs)
				}
			]
		}
