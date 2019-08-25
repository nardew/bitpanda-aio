import enum

class RestCallType(enum.Enum):
	GET = enum.auto()
	POST = enum.auto()
	DELETE = enum.auto()

class OrderSide(enum.Enum):
	BUY = "BUY"
	SELL = "SELL"
