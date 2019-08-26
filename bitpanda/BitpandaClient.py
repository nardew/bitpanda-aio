import asyncio
import aiohttp
import ssl
import logging
import datetime
import pytz
from typing import List, Callable, Any

from bitpanda.Pair import Pair
from bitpanda.websockets import Websocket, PriceWebsocket, OrderbookWebsocket, AccountWebsocket, CandlesticksWebsocket, \
	MarketTickerWebsocket, CandlesticksSubscriptionParams
from bitpanda import enums

logger = logging.getLogger(__name__)

class BitpandaClient(object):
	REST_API_URI = "https://api.exchange.bitpanda.com/public/v1/"

	def __init__(self, certificate_path : str = None, api_key : str = None, api_trace_log : bool = False) -> None:
		self.api_key = api_key
		self.api_trace_log = api_trace_log

		self.rest_session = None

		self.ws_subscriptions = []

		self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
		self.ssl_context.load_verify_locations(certificate_path)

	async def get_currencies(self) -> dict:
		return await self._create_get("currencies")

	async def get_account_balances(self) -> dict:
		return await self._create_get("account/balances", headers = self._get_header_api_key())

	async def get_account_fees(self) -> dict:
		return await self._create_get("account/fees", headers = self._get_header_api_key())

	async def get_account_orders(self, from_timestamp : datetime.datetime = None, to_timestamp : datetime.datetime = None,
	                             pair : Pair = None, with_cancelled_and_rejected : str = None, with_just_filled_inactive : str = None,
	                             max_page_size : str = None, cursor : str = None) -> dict:
		params = BitpandaClient._clean_request_params({
			"from": from_timestamp,
			"to": to_timestamp,
			"instrument_code": pair,
			"with_cancelled_and_rejected": with_cancelled_and_rejected,
			"with_just_filled_inactive": with_just_filled_inactive,
			"max_page_size": max_page_size,
			"cursor": cursor,
		})

		try:
			params["from"] = params["from"].astimezone(pytz.utc).isoformat()
		except KeyError:
			pass

		try:
			params["to"] = params["to"].astimezone(pytz.utc).isoformat()
		except KeyError:
			pass

		return await self._create_get("account/orders", params = params, headers = self._get_header_api_key())

	async def get_account_order(self, order_id : str) -> dict:
		return await self._create_get("account/orders/" + order_id, headers=self._get_header_api_key())

	async def get_account_order_trades(self, order_id : str) -> dict:
		return await self._create_get("account/orders/" + order_id + "/trades", headers = self._get_header_api_key())

	async def get_account_trades(self, from_timestamp : datetime.datetime = None, to_timestamp : datetime.datetime = None,
	                             pair : Pair = None, max_page_size : str = None, cursor : str = None) -> dict:
		params = BitpandaClient._clean_request_params({
			"from": from_timestamp,
			"to": to_timestamp,
			"instrument_code": pair,
			"max_page_size": max_page_size,
			"cursor": cursor,
		})

		try:
			params["from"] = params["from"].astimezone(pytz.utc).isoformat()
		except KeyError:
			pass

		try:
			params["to"] = params["to"].astimezone(pytz.utc).isoformat()
		except KeyError:
			pass

		return await self._create_get("account/trades", params = params, headers = self._get_header_api_key())

	async def get_account_trade(self, trade_id : str) -> dict:
		return await self._create_get("account/trades/" + trade_id, headers = self._get_header_api_key())

	async def get_account_trading_volume(self) -> dict:
		return await self._create_get("account/trading-volume", headers = self._get_header_api_key())

	async def create_market_order(self, pair : Pair, side : enums.OrderSide, amount : str) -> dict:
		data = {
			"instrument_code": str(pair),
			"side": side.value,
			"type": "MARKET",
			"amount": amount
		}

		return await self._create_post("account/orders", data = data, headers = self._get_header_api_key())

	async def create_limit_order(self, pair : Pair, side : enums.OrderSide, amount : str, limit_price : str) -> dict:
		data = {
			"instrument_code": str(pair),
			"side": side.value,
			"type": "LIMIT",
			"amount": amount,
			"price": limit_price
		}

		return await self._create_post("account/orders", data = data, headers = self._get_header_api_key())

	async def create_stop_limit_order(self, pair : Pair, side : enums.OrderSide, amount : str, limit_price : str, stop_price : str) -> dict:
		data = {
			"instrument_code": str(pair),
			"side": side.value,
			"type": "STOP",
			"amount": amount,
			"price": limit_price,
			"trigger_price": stop_price
		}

		return await self._create_post("account/orders", data = data, headers = self._get_header_api_key())

	async def delete_account_orders(self, pair : Pair = None) -> dict:
		params = BitpandaClient._clean_request_params({
			"instrument_code": pair,
		})

		return await self._create_delete("account/orders", params = params, headers = self._get_header_api_key())

	async def delete_account_order(self, order_id : str) -> dict:
		return await self._create_delete("account/orders/" + order_id, headers=self._get_header_api_key())

	async def get_candlesticks(self, pair : Pair, unit : enums.TimeUnit, period : str, from_timestamp : datetime.datetime, to_timestamp : datetime.datetime) -> dict:
		params = {
			"unit": unit.value,
			"period": period,
			"from": from_timestamp.astimezone(pytz.utc).isoformat(),
			"to": to_timestamp.astimezone(pytz.utc).isoformat(),
		}

		return await self._create_get("candlesticks/" + str(pair), params = params)

	async def get_instruments(self) -> dict:
		return await self._create_get("instruments")

	async def get_order_book(self, pair : Pair, level : str = None) -> dict:
		params = BitpandaClient._clean_request_params({
			"level": level,
		})

		return await self._create_get("order-book/" + str(pair), params = params)

	async def get_time(self) -> dict:
		return await self._create_get("time")

	def subscribe_prices_ws(self, pairs : List[Pair], callbacks : List[Callable[[dict], Any]] = None) -> None:
		self._subscribe_ws(PriceWebsocket(pairs, callbacks, self.ssl_context))

	def subscribe_order_book_ws(self, pairs : List[Pair], depth : str, callbacks : List[Callable[[dict], Any]] = None) -> None:
		self._subscribe_ws(OrderbookWebsocket(pairs, depth, callbacks, self.ssl_context))

	def subscribe_account_ws(self, callbacks : List[Callable[[dict], Any]] = None) -> None:
		self._subscribe_ws(AccountWebsocket(self.api_key, callbacks, self.ssl_context))

	def subscribe_candlesticks_ws(self, subscription_params : List[CandlesticksSubscriptionParams], callbacks : List[Callable[[dict], Any]] = None) -> None:
		self._subscribe_ws(CandlesticksWebsocket(subscription_params, callbacks, self.ssl_context))

	def subscribe_market_ticker_ws(self, pairs : List[Pair], callbacks : List[Callable[[dict], Any]] = None) -> None:
		self._subscribe_ws(MarketTickerWebsocket(pairs, callbacks, self.ssl_context))

	async def start_websockets(self) -> None:
		if len(self.ws_subscriptions):
			done, pending = await asyncio.wait([asyncio.create_task(ws_subscription.run()) for ws_subscription in self.ws_subscriptions], return_when = asyncio.FIRST_EXCEPTION)
			for task in done:
				try:
					task.result()
				except Exception as e:
					logger.exception(f"Unrecoverable exception occurred while processing websockets: {e}")
					logger.info("All websockets scheduled for shutdown")
					for task in pending:
						if not task.cancelled():
							task.cancel()

	async def _create_get(self, resource : str, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.GET, resource, None, params, headers)

	async def _create_post(self, resource : str, data : dict = None, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.POST, resource, data, params, headers)

	async def _create_delete(self, resource : str, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.DELETE, resource, None, params, headers)

	async def _create_rest_call(self, rest_call_type : enums.RestCallType, resource : str, data : dict = None, params : dict = None, headers : dict = None) -> dict:
		if rest_call_type == enums.RestCallType.GET:
			rest_call = self._get_rest_session().get(BitpandaClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
		elif rest_call_type == enums.RestCallType.POST:
			rest_call = self._get_rest_session().post(BitpandaClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
		elif rest_call_type == enums.RestCallType.DELETE:
			rest_call = self._get_rest_session().delete(BitpandaClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
		else:
			raise Exception(f"Unsupported REST call type {rest_call_type}.")

		logger.debug(f"> resource [{resource}], params [{params}], headers [{headers}], data [{data}]")
		async with rest_call as response:
			status_code = response.status
			response_text = await response.text()

			logger.debug(f"<: status [{status_code}], response [{response_text}]")

			return {
				"status_code": status_code,
				"response": response_text
			}

	def _is_ws_already_subscribed(self, ws : Websocket) -> bool:
		for ws_subscription in self.ws_subscriptions:
			if ws_subscription.get_websocket_id() == ws.get_websocket_id():
				return True

		return False

	def _subscribe_ws(self, ws : Websocket) -> None:
		if self._is_ws_already_subscribed(ws):
			raise Exception(f"ERROR: Attempt to subscribe duplicate websocket {ws.get_websocket_id()}")
		else:
			self.ws_subscriptions.append(ws)

	def _get_rest_session(self) -> aiohttp.ClientSession:
		if self.rest_session is not None:
			return self.rest_session

		if self.api_trace_log:
			trace_config = aiohttp.TraceConfig()
			trace_config.on_request_start.append(BitpandaClient._on_request_start)
			trace_config.on_request_end.append(BitpandaClient._on_request_end)
			trace_configs = [trace_config]
		else:
			trace_configs = None

		self.rest_session = aiohttp.ClientSession(trace_configs=trace_configs)

		return self.rest_session

	def _get_header_api_key(self):
		header = {
			"Authorization": "Bearer " + self.api_key
		}

		return header

	@staticmethod
	def _clean_request_params(params : dict) -> dict:
		res = {}
		for key, value in params.items():
			if value is not None:
				res[key] = str(value)

		return res

	async def close(self) -> None:
		session = self._get_rest_session()
		if session is not None:
			await session.close()

	async def _on_request_start(session, trace_config_ctx, params) -> None:
		logger.debug(f"> Context: {trace_config_ctx}")
		logger.debug(f"> Params: {params}")

	async def _on_request_end(session, trace_config_ctx, params) -> None:
		logger.debug(f"< Context: {trace_config_ctx}")
		logger.debug(f"< Params: {params}")
