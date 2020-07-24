"""Summary
"""
from intersection import Intersection
from config import *



class Corridor:

	def __init__(self, intersections):
		self.intx_1 = Intersection(intersections[0])
		self.intx_2 = Intersection(intersections[1])

	def aapi_post_manage(self, time, timeSta, timeTrans, acycle):
		# 1. check-in
		if (self.intx_1._bus_enter_handler(time)):
			# TODO: update state
			None
		if (self.intx_2._bus_enter_handler(time)):
			# TODO: update state
			None

		# 2. send new state and previous reward to DQN
		# 3. apply action

		# 4. check-out and get reward
		if (self.intx_1._bus_out_handler(time)):
			# TODO: update state
			# TODO: get reward
			None
		if (self.intx_2._bus_out_handler(time)):
			# TODO: update state
			# TODO: get reward
			None
		return 0

