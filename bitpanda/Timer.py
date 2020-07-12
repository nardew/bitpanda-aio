import time
import logging

LOG = logging.getLogger(__name__)

class Timer(object):
	def __init__(self, name, active = True):
		self.name = name
		self.active = active

		self.current_milli_time = lambda: int(round(time.time() * 1000))

	def __enter__(self):
		self.start_tmstmp = self.current_milli_time()

	def __exit__(self, type, value, traceback):
		if self.active:
			LOG.debug(f'Timer {self.name} finished. Took {(self.current_milli_time() - self.start_tmstmp)} ms.')