import enum

class RestCallType(enum.Enum):
	GET = enum.auto()
	POST = enum.auto()
	DELETE = enum.auto()

class OrderSide(enum.Enum):
	BUY = "BUY"
	SELL = "SELL"

class TimeInForce(enum.Enum):
	GOOD_TILL_CANCELLED = "GOOD_TILL_CANCELLED"
	IMMEDIATE_OR_CANCELLED = "IMMEDIATE_OR_CANCELLED"

class TimeUnit(enum.Enum):
	MINUTES = "MINUTES"
	HOURS = "HOURS"
	DAYS = "DAYS"
	WEEKS = "WEEKS"
	MONTHS = "MONTHS"
