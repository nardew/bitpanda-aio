import websockets
import json
import logging
import asyncio
from abc import ABC, abstractmethod

from bitpanda.Pair import Pair
from bitpanda import enums

logger = logging.getLogger(__name__)

class Subscription(ABC):
	def __init__(self, callbacks = None):
		self.callbacks = callbacks

	@abstractmethod
	def get_channel_name(self):
		pass

	@abstractmethod
	def get_channel_subscription_message(self):
		pass

	async def process_message(self, response):
		await self.process_callbacks(response)

	async def process_callbacks(self, response):
		if self.callbacks is not None:
			await asyncio.gather(*[asyncio.create_task(cb(response)) for cb in self.callbacks])

	@staticmethod
	def _get_subscription_instrument_codes(pairs):
		return [pair.base + "_" + pair.quote for pair in pairs]

class SubscriptionMgr(object):
	WEB_SOCKET_URI = "wss://streams.exchange.bitpanda.com"

	def __init__(self, ssl_context = None):
		self.ssl_context = ssl_context

		self.subscriptions = []

	async def run(self):
		try:
			# main loop ensuring proper reconnection after a graceful connection termination by the remote server
			while True:
				logger.debug(f"Initiating websocket connection.")
				async with websockets.connect(SubscriptionMgr.WEB_SOCKET_URI, ssl = self.ssl_context) as websocket:
					subscription_message = self._create_subscription_message()
					logger.debug(f"> {subscription_message}")
					await websocket.send(json.dumps(subscription_message))

					# start processing incoming messages
					while True:
						response = json.loads(await websocket.recv())
						logger.debug(f"< {response}")

						# subscription positive response
						if response['type'] == "SUBSCRIPTIONS":
							logger.info(f"Subscription confirmed for channels [" + ",".join([channel["name"] for channel in response["channels"]]) + "]")

						# subscription negative response
						elif response['type'] == "ERROR":
							raise Exception(f"Subscription error. Request [{json.dumps(subscription_message)}] Response [{json.dumps(response)}]")

						# remote termination with an opportunity to reconnect
						elif response["type"] == "CONNECTION_CLOSING":
							logger.warning(f"Server is performing connection termination with an opportunity to reconnect.")
							break

						# heartbeat message
						elif response["type"] == "HEARTBEAT":
							pass

						# regular message
						else:
							await self.process_message(response)
		except asyncio.CancelledError:
			logger.warning(f"Websocket requested to be shutdown.")
		except Exception:
			logger.error(f"Exception occurred. Websocket will be closed.")
			raise

	def _create_subscription_message(self):
		return {
			"type": "SUBSCRIBE",
			"channels": [
				subscription.get_channel_subscription_message() for subscription in self.subscriptions
			]
		}

	def add_subscription(self, subscription : Subscription) -> None:
		if self._is_channel_already_subscribed(subscription):
			raise Exception(f"ERROR: Attempt to subscribe duplicate channel {subscription.get_channel_name()}")
		else:
			self.subscriptions.append(subscription)

	def _is_channel_already_subscribed(self, new_subscription : Subscription) -> bool:
		for subscription in self.subscriptions:
			if subscription.get_channel_name() == new_subscription.get_channel_name():
				return True

		return False

	async def process_message(self, response):
		for subscription in self.subscriptions:
			if subscription.get_channel_name() == response["channel_name"]:
				await subscription.process_message(response)
				break

class AccountSubscription(Subscription):
	def __init__(self, api_key, callbacks = None):
		super().__init__(callbacks)

		self.api_key = api_key

	def get_channel_name(self):
		return "ACCOUNT_HISTORY"

	def get_channel_subscription_message(self):
		return {
			"name": self.get_channel_name(),
			"api_token": self.api_key
		}

class PricesSubscription(Subscription):
	def __init__(self, pairs, callbacks = None):
		super().__init__(callbacks)

		self.pairs = pairs

	def get_channel_name(self):
		return "PRICE_TICKS"

	def get_channel_subscription_message(self):
		return {
			"name": self.get_channel_name(),
			"instrument_codes": Subscription._get_subscription_instrument_codes(self.pairs)
		}

class OrderbookSubscription(Subscription):
	def __init__(self, pairs, depth, callbacks = None):
		super().__init__(callbacks)

		self.pairs = pairs
		self.depth = depth

	def get_channel_name(self):
		return "ORDER_BOOK"

	def get_channel_subscription_message(self):
		return {
			"name": self.get_channel_name(),
			"depth": self.depth,
			"instrument_codes": Subscription._get_subscription_instrument_codes(self.pairs)
		}

class CandlesticksSubscriptionParams(object):
	def __init__(self, pair : Pair, unit : enums.TimeUnit, period):
		self.pair = pair
		self.unit = unit
		self.period = period

class CandlesticksSubscription(Subscription):
	def __init__(self, subscription_params, callbacks = None):
		super().__init__(callbacks)

		self.subscription_params = subscription_params

	def get_channel_name(self):
		return "CANDLESTICKS"

	def get_channel_subscription_message(self):
		return {
			"name": self.get_channel_name(),
			"properties": [{
				"instrument_code": params.pair.base + "_" + params.pair.quote,
				"time_granularity": {
					"unit": params.unit.value,
					"period": params.period
				}
			} for params in self.subscription_params]
		}

class MarketTickerSubscription(Subscription):
	def __init__(self, pairs, callbacks = None):
		super().__init__(callbacks)

		self.pairs = pairs

	def get_channel_name(self):
		return "MARKET_TICKER"

	def get_channel_subscription_message(self):
		return {
			"name": self.get_channel_name(),
			"instrument_codes": Subscription._get_subscription_instrument_codes(self.pairs)
		}
