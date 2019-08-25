import asyncio
import aiohttp
import ssl
import logging
import datetime
import pytz

from bitpanda.Pair import Pair
from bitpanda.constants import REST_API_URI
from bitpanda.websockets import WebSocket, PriceWebSocket, OrderBookWebSocket, AccountWebSocket, CandlesticksWebSocket, MarketTickerWebSocket
from bitpanda import enums

logger = logging.getLogger(__name__)

class BitpandaClient(object):
	def __init__(self, certificate_path : str = None, api_key : str = None, api_trace_log : bool = False) -> None:
		self.api_key = api_key
		self.api_trace_log = api_trace_log

		self.rest_session = None

		self.ws_subscriptions = []

		self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
		self.ssl_context.load_verify_locations(certificate_path)

	def _get_rest_session(self) -> aiohttp.ClientSession:
		if self.rest_session is not None:
			return self.rest_session

		if self.api_trace_log:
			trace_config = aiohttp.TraceConfig()
			trace_config.on_request_start.append(BitpandaClient.on_request_start)
			trace_config.on_request_end.append(BitpandaClient.on_request_end)
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
				res[key] = value

		return res

	async def close(self) -> None:
		session = self._get_rest_session()
		if session is not None:
			await session.close()

	async def on_request_start(session, trace_config_ctx, params) -> None:
		print(f"> Context: {trace_config_ctx}")
		print(f"> Params: {params}")

	async def on_request_end(session, trace_config_ctx, params) -> None:
		print(f"< Context: {trace_config_ctx}")
		print(f"< Params: {params}")

	async def get_currencies(self) -> dict:
		return await self._create_get("currencies")

	async def get_account_balances(self) -> dict:
		return await self._create_get("account/balances", headers = self._get_header_api_key())

	async def get_account_fees(self) -> dict:
		return await self._create_get("account/fees", headers = self._get_header_api_key())

	async def get_account_orders(self, from_timestamp : datetime.datetime = None, to_timestamp : datetime.datetime = None, pair : Pair = None, with_cancelled_and_rejected : str = None, with_just_filled_inactive : str = None, max_page_size : str = None, cursor : str = None) -> dict:
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

	async def get_account_trades(self, from_timestamp : datetime.datetime = None, to_timestamp : datetime.datetime = None, pair : Pair = None, max_page_size : str = None, cursor : str = None) -> dict:
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

	async def create_account_order_market(self, base : str, quote : str, side : enums.OrderSide, amount) -> dict:
		data = {
			"instrument_code": base + "_" + quote,
			"side": side.value,
			"type": "MARKET",
			"amount": amount
		}

		return await self._create_post("account/orders", data = data, headers = self._get_header_api_key())

	async def create_account_order_limit(self, base : str, quote : str, side : enums.OrderSide, amount, limit_price) -> dict:
		data = {
			"instrument_code": base + "_" + quote,
			"side": side.value,
			"type": "LIMIT",
			"amount": amount,
			"price": limit_price
		}

		return await self._create_post("account/orders", data = data, headers = self._get_header_api_key())

	async def create_account_order_stop_limit(self, base : str, quote : str, side : enums.OrderSide, amount, limit_price, stop_price) -> dict:
		data = {
			"instrument_code": base + "_" + quote,
			"side": side.value,
			"type": "STOP",
			"amount": amount,
			"price": limit_price,
			"trigger_price": stop_price
		}

		return await self._create_post("account/orders", data = data, headers = self._get_header_api_key())

	async def delete_account_orders(self, base : str = None, quote : str = None) -> dict:
		params = BitpandaClient._clean_request_params({
			"instrument_code": base + "_" + quote,
		})

		return await self._create_delete("account/orders", params = params, headers = self._get_header_api_key())

	async def delete_account_order(self, order_id) -> dict:
		return await self._create_delete("account/orders/" + order_id, headers=self._get_header_api_key())

	async def get_candlesticks(self, base : str, quote : str, unit : str, period : str, from_timestamp : datetime.datetime, to_timestamp : datetime.datetime) -> dict:
		params = {
			"unit": unit,
			"period": period,
			"from": from_timestamp.astimezone(pytz.utc).isoformat(),
			"to": to_timestamp.astimezone(pytz.utc).isoformat(),
		}

		return await self._create_get("candlesticks/" + base + "_" + quote, params = params)

	async def get_instruments(self) -> dict:
		return await self._create_get("instruments")

	async def get_order_book(self, base : str, quote : str, level : str = None) -> dict:
		params = BitpandaClient._clean_request_params({
			"level": level,
		})

		return await self._create_get("order-book/" + base + "_" + quote, params = params)

	async def get_time(self) -> dict:
		return await self._create_get("time")

	async def _create_get(self, resource : str, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.GET, resource, None, params, headers)

	async def _create_post(self, resource : str, data : dict = None, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.POST, resource, data, params, headers)

	async def _create_delete(self, resource : str, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.DELETE, resource, None, params, headers)

	async def _create_rest_call(self, rest_call_type : enums.RestCallType, resource : str, data : dict = None, params : dict = None, headers : dict = None) -> dict:
		if rest_call_type == enums.RestCallType.GET:
			rest_call = self._get_rest_session().get(REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
		elif rest_call_type == enums.RestCallType.POST:
			rest_call = self._get_rest_session().post(REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
		elif rest_call_type == enums.RestCallType.DELETE:
			rest_call = self._get_rest_session().delete(REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
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

	def _is_ws_already_subscribed(self, ws : WebSocket) -> bool:
		for ws_subscription in self.ws_subscriptions:
			if ws_subscription.get_websocket_id() == ws.get_websocket_id():
				return True

		return False

	def _subscribe_ws(self, ws : WebSocket) -> None:
		if self._is_ws_already_subscribed(ws):
			raise Exception(f"ERROR: Attempt to subscribe duplicate websocket {ws.get_websocket_id()}")
		else:
			self.ws_subscriptions.append(ws)

	def subscribe_prices_ws(self, pairs, callbacks = None) -> None:
		self._subscribe_ws(PriceWebSocket(pairs, callbacks, self.ssl_context))

	def subscribe_order_book_ws(self, pairs, depth, callbacks = None) -> None:
		self._subscribe_ws(OrderBookWebSocket(pairs, depth, callbacks, self.ssl_context))

	def subscribe_account_ws(self, callbacks = None) -> None:
		self._subscribe_ws(AccountWebSocket(self.api_key, callbacks, self.ssl_context))

	def subscribe_candlesticks_ws(self, subscription_params, callbacks = None) -> None:
		self._subscribe_ws(CandlesticksWebSocket(subscription_params, callbacks, self.ssl_context))

	def subscribe_market_ticker_ws(self, pairs, callbacks = None) -> None:
		self._subscribe_ws(MarketTickerWebSocket(pairs, callbacks, self.ssl_context))

	async def start_websockets(self) -> None:
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
