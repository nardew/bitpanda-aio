import asyncio
import aiohttp
import ssl
import logging
import datetime
import pytz
import json
from typing import List, Callable, Any

from bitpanda.Pair import Pair
from bitpanda.subscriptions import Subscription, SubscriptionMgr, PricesSubscription, OrderbookSubscription, AccountSubscription, CandlesticksSubscription, \
	MarketTickerSubscription, CandlesticksSubscriptionParams
from bitpanda import enums
from bitpanda.Timer import Timer

LOG = logging.getLogger(__name__)

class BitpandaClient(object):
	REST_API_URI = "https://api.exchange.bitpanda.com/public/v1/"

	def __init__(self, certificate_path : str = None, api_key : str = None, api_trace_log : bool = False) -> None:
		self.api_key = api_key
		self.api_trace_log = api_trace_log

		self.rest_session = None

		self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
		self.ssl_context.load_verify_locations(certificate_path)

		self.subscription_sets = []

	async def get_currencies(self) -> dict:
		return await self._create_get("currencies")

	async def get_account_balances(self) -> dict:
		return await self._create_get("account/balances", headers = self._get_header_api_key())

	async def get_account_fees(self) -> dict:
		return await self._create_get("account/fees", headers = self._get_header_api_key())

	async def get_account_orders(self, from_timestamp : datetime.datetime = None, to_timestamp : datetime.datetime = None,
	                             pair : Pair = None, with_cancelled_and_rejected : str = None, with_just_filled_inactive : str = None,
	                             with_just_orders : str = None, max_page_size : str = None, cursor : str = None) -> dict:
		params = BitpandaClient._clean_request_params({
			"instrument_code": pair,
			"with_cancelled_and_rejected": with_cancelled_and_rejected,
			"with_just_filled_inactive": with_just_filled_inactive,
			"with_just_orders": with_just_orders,
			"max_page_size": max_page_size,
			"cursor": cursor,
		})

		if from_timestamp is not None:
			params["from"] = from_timestamp.astimezone(pytz.utc).isoformat()

		if to_timestamp is not None:
			params["to"] = to_timestamp.astimezone(pytz.utc).isoformat()

		return await self._create_get("account/orders", params = params, headers = self._get_header_api_key())

	async def get_account_order(self, order_id : str) -> dict:
		return await self._create_get("account/orders/" + order_id, headers=self._get_header_api_key())

	async def get_account_order_trades(self, order_id : str) -> dict:
		return await self._create_get("account/orders/" + order_id + "/trades", headers = self._get_header_api_key())

	async def get_account_trades(self, from_timestamp : datetime.datetime = None, to_timestamp : datetime.datetime = None,
	                             pair : Pair = None, max_page_size : str = None, cursor : str = None) -> dict:
		params = BitpandaClient._clean_request_params({
			"instrument_code": pair,
			"max_page_size": max_page_size,
			"cursor": cursor,
		})

		if from_timestamp is not None:
			params["from"] = from_timestamp.astimezone(pytz.utc).isoformat()

		if to_timestamp is not None:
			params["to"] = to_timestamp.astimezone(pytz.utc).isoformat()

		return await self._create_get("account/trades", params = params, headers = self._get_header_api_key())

	async def get_account_trade(self, trade_id : str) -> dict:
		return await self._create_get("account/trades/" + trade_id, headers = self._get_header_api_key())

	async def get_account_trading_volume(self) -> dict:
		return await self._create_get("account/trading-volume", headers = self._get_header_api_key())

	async def create_market_order(self, pair : Pair, side : enums.OrderSide, amount : str, client_id : str = None) -> dict:
		data = {
			"instrument_code": str(pair),
			"side": side.value,
			"type": "MARKET",
			"amount": amount
		}

		if client_id is not None:
			data['client_id'] = client_id

		return await self._create_post("account/orders", data = data, headers = self._get_header_api_key())

	async def create_limit_order(self, pair : Pair, side : enums.OrderSide, amount : str, limit_price : str, time_in_force : enums.TimeInForce = None, client_id : str = None) -> dict:
		data = {
			"instrument_code": str(pair),
			"side": side.value,
			"type": "LIMIT",
			"amount": amount,
			"price": limit_price
		}

		if client_id is not None:
			data['client_id'] = client_id

		if time_in_force is not None:
			data['time_in_force'] = time_in_force.value

		return await self._create_post("account/orders", data = data, headers = self._get_header_api_key())

	async def create_stop_limit_order(self, pair : Pair, side : enums.OrderSide, amount : str, limit_price : str, stop_price : str,
	                                  time_in_force : enums.TimeInForce = None, client_id : str = None) -> dict:
		data = {
			"instrument_code": str(pair),
			"side": side.value,
			"type": "STOP",
			"amount": amount,
			"price": limit_price,
			"trigger_price": stop_price
		}

		if client_id is not None:
			data['client_id'] = client_id

		if time_in_force is not None:
			data['time_in_force'] = time_in_force.value

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

	def compose_subscriptions(self, subscriptions : List[Subscription]) -> None:
		self.subscription_sets.append(subscriptions)

	async def start_subscriptions(self) -> None:
		if len(self.subscription_sets):
			done, pending = await asyncio.wait(
				[asyncio.create_task(SubscriptionMgr(subscriptions, self.api_key, self.ssl_context).run()) for subscriptions in self.subscription_sets],
				return_when = asyncio.FIRST_EXCEPTION
			)
			for task in done:
				try:
					task.result()
				except Exception as e:
					LOG.exception(f"Unrecoverable exception occurred while processing messages: {e}")
					LOG.info("All websockets scheduled for shutdown")
					for task in pending:
						if not task.cancelled():
							task.cancel()
		else:
			raise Exception("ERROR: There are no subscriptions to be started.")

	async def close(self) -> None:
		session = self._get_rest_session()
		if session is not None:
			await session.close()

	async def _create_get(self, resource : str, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.GET, resource, None, params, headers)

	async def _create_post(self, resource : str, data : dict = None, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.POST, resource, data, params, headers)

	async def _create_delete(self, resource : str, params : dict = None, headers : dict = None) -> dict:
		return await self._create_rest_call(enums.RestCallType.DELETE, resource, None, params, headers)

	async def _create_rest_call(self, rest_call_type : enums.RestCallType, resource : str, data : dict = None, params : dict = None, headers : dict = None) -> dict:
		with Timer('RestCall'):
			if rest_call_type == enums.RestCallType.GET:
				rest_call = self._get_rest_session().get(BitpandaClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
			elif rest_call_type == enums.RestCallType.POST:
				rest_call = self._get_rest_session().post(BitpandaClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
			elif rest_call_type == enums.RestCallType.DELETE:
				rest_call = self._get_rest_session().delete(BitpandaClient.REST_API_URI + resource, json = data, params = params, headers = headers, ssl = self.ssl_context)
			else:
				raise Exception(f"Unsupported REST call type {rest_call_type}.")

			LOG.debug(f"> rest type [{rest_call_type.name}], resource [{resource}], params [{params}], headers [{headers}], data [{data}]")
			async with rest_call as response:
				status_code = response.status
				response_body = await response.text()

				LOG.debug(f"<: status [{status_code}], response [{response_body}]")

				if len(response_body) > 0:
					response_body = json.loads(response_body)

				return {
					"status_code": status_code,
					"headers": response.headers,
					"response": response_body
				}

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

	async def _on_request_start(session, trace_config_ctx, params) -> None:
		LOG.debug(f"> Context: {trace_config_ctx}")
		LOG.debug(f"> Params: {params}")

	async def _on_request_end(session, trace_config_ctx, params) -> None:
		LOG.debug(f"< Context: {trace_config_ctx}")
		LOG.debug(f"< Params: {params}")
