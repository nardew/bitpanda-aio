class Pair(object):
	def __init__(self, base, quote):
		self.base = base
		self.quote = quote

	def __str__(self):
		return self.base + "_" + self.quote
