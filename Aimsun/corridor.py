"""Summary
"""
from intersection import Intersection
from config import *



class Corridor:

	def __init__(self, intersections):
		self.intx_1 = Intersection(intersections[0])
		self.intx_2 = Intersection(intersections[1])

	def POZ_handler(self, time, timeSta, timeTrans, acycle):
		return 0

