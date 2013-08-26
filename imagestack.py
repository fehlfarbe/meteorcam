#! /usr/bin/env python

class Imagestack(object):

	def __init__(self, maximages = 0):
		self._max = maximages
		self._images = []

	def add(self, img, time):
		self._images.append({'img' : img,
							'time' : time})
		
		if self._max != 0:
			while len(self._images) >= self._max:
				self._images.pop(0)
				
	def addList(self, lst):
		self._images.append(lst)
		
		if self._max != 0:
			while len(self._images) >= self._max:
				self._images.pop(0)

	def size(self):
		return len(self._images)


	def getImages(self):
		return self._images
		


