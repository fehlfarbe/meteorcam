#! /usr/bin/env python
#
#	gets images from video/device and detects
#	motions
#

import copy
import sys
import time
import colorsys
import cv2.cv as cv
import cv2
import imagestack
import thread
import os.path
import array
import util
import ConfigParser

class Detector(object):

	def __init__(self, threadnr, config):
		## text
		self._fontsize = 0.5
		self._fontcolor = (255, 255, 255)
		self._font = cv.InitFont(cv.CV_FONT_HERSHEY_DUPLEX, self._fontsize, self._fontsize, cv.CV_AA)
		self._texttl = ""

		## motion detection
		self._deNoiseLevel = 0
		self._darkframe = None
		self._mask = None
		self._avgLevel = 0.01
		self._prevFrames = 10
		self._postFrames = 50
		self._detectThresh = 20
		self._maxVideoGap = 10

		## postprocessing
		self._drawRect = True
		self._minRectArea = 10
		self._maxRectArea = 400
		self._bRectOffset = 20
		self._videoDir = "./capture/2013/08/"		

		## xxxxx
		self._showWindow = True

		## video
		self._videoInput = None
		self._videoSize = (640, 480)
		self._fps = 25

		## thread
		self._thread = threadnr
		self._run = True
		self.active = False

		self.loadConfig(config)


	######## Load Config file #########
	def loadConfig(self, configfile):
		self.log("load config " + configfile)
		
		defaults = {
				## text
				'fontsize' : self._fontsize,
				'fontcolor' : self._fontcolor,
				'texttl' : str(self._texttl),
				## motion detection
				'deNoiseLevel' : self._deNoiseLevel,
				'darkframe' : self._darkframe,
				'mask' : self._mask,
				'avgLevel' : self._avgLevel,
				'prevFrames' : self._prevFrames,
				'postFrames' : self._postFrames,
				'detectThresh' : self._detectThresh,
				'maxVideoGap' : self._maxVideoGap,
				## postprocessing
				'drawRect' : str(self._drawRect),
				'minRectArea' : self._minRectArea,
				'maxRectArea' : self._maxRectArea,
				'bRectOffset' : self._bRectOffset,
				'videoDir' : str(self._videoDir),				
				## xxxxx
				'showWindow' : str(self._showWindow),
				## video
				'videoInput' : self._videoInput,
				'videoSize' : self._videoSize,
				'fps' : self._fps
				}
		config = ConfigParser.RawConfigParser(defaults)
		config.read( configfile )
		
		## text
		self._fontsize = config.getfloat('DEFAULT', 'fontsize')
		self._fontcolor = config.get('DEFAULT', 'fontcolor')
		self._font = cv.InitFont(cv.CV_FONT_HERSHEY_DUPLEX, self._fontsize, self._fontsize, cv.CV_AA)
		self._texttl = config.get('DEFAULT', 'texttl')

		## motion detection
		self._deNoiseLevel = config.getfloat('DEFAULT', 'deNoiseLevel')
		df = config.get('DEFAULT', 'darkframe')
		if df != None:
			self._darkframe = cv.LoadImage(df)
		self._mask = config.get('DEFAULT', 'mask')
		self._avgLevel = config.getfloat('DEFAULT', 'avgLevel')
		self._prevFrames = config.getfloat('DEFAULT', 'prevFrames')
		self._postFrames = config.getfloat('DEFAULT', 'postFrames')
		self._detectThresh = config.getfloat('DEFAULT', 'detectThresh')
		self._maxVideoGap = config.getfloat('DEFAULT', 'maxVideoGap')

		## postprocessing
		self._drawRect = config.getboolean('DEFAULT', 'drawRect')
		self._minRectArea = config.getfloat('DEFAULT', 'minRectArea')
		self._maxRectArea = config.getfloat('DEFAULT', 'maxRectArea')
		self._bRectOffset = config.getint('DEFAULT', 'bRectOffset')
		self._videoDir = config.get('DEFAULT', 'videoDir')

		## xxxxx
		self._showWindow = config.getboolean('DEFAULT', 'showWindow')

		## video
		self._videoInput = config.get('DEFAULT', 'videoInput')
		self._videoSize = config.get('DEFAULT', 'videoSize')
		self._fps = config.getfloat('DEFAULT', 'fps')

		self.log("config loaded")

	######## Log ########
	def log(self, string):
		print("[" + str(self._thread) + "] " + str(string))


	######## stop detection
	def stop(self):
		self._run = False

	######## start detection
	def start(self, config):

		self.loadConfig(config)

		if self._videoInput :
			self.active = True
			thread.start_new_thread(self.detect, ())
		else:
			self.log("No video input specified!")


	######## detect ######
	def detect(self):	

		self.log("Start detection thread")
		try:
			capture = cv.CaptureFromCAM(int(self._videoInput))
			cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, self._videoSize[0])
			cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, self._videoSize[1])
			cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FPS, self._fps)
			self.log("Capture from cam")		
		except:
			capture = cv.CaptureFromFile(self._videoInput)
			self.log("Capture from file " + self._videoInput)
		
		runAvg = None
		runAvgDisplay = None
		differenceImg = None
		historyBuffer = imagestack.Imagestack(self._prevFrames)
		videoGap = self._maxVideoGap
		postFrames = 0
		frameCount = float(0)
		detect = False
		newVideo = True

		### capture loop ###

		### testwindow
		if self._showWindow:
			self.log("Show window")
			cv.NamedWindow("Thread " + str(self._thread), 1)

		while self._run:
			ts = time.time()
			frame = cv.QueryFrame(capture)
			print time.time() - ts
			ts = (ts+time.time()) / 2

			videoGap += 1

			if frame:

				frameSize = cv.GetSize(frame)

				frameCount += 1

				if 1/frameCount < self._avgLevel and not detect:
					#self.log("frames: " + str(1/frameCount))
					self.log("start detection")
					detect = True
				
		
				if self._darkframe:
					if frameSize == cv.GetSize(self._darkframe):
						cv.Sub( frame, self._darkframe, frame )

				## detect motion
				if not runAvg:
					runAvg = cv.CreateImage( frameSize, cv.IPL_DEPTH_32F, 3 )
				if not runAvgDisplay:
					runAvgDisplay = cv.CloneImage( frame )
				if not differenceImg:
					differenceImg = cv.CloneImage( frame )
	
				if self._deNoiseLevel > 0:
					cv.Smooth( frame, frame, cv.CV_MEDIAN, self._deNoiseLevel)
				cv.RunningAvg( frame, runAvg, self._avgLevel, self._mask )
				cv.ConvertScale( runAvg, runAvgDisplay, 1.0, 0.0 )
				cv.AbsDiff( frame, runAvgDisplay, differenceImg )

				grayImg = cv.CreateImage((differenceImg.width,differenceImg.height),differenceImg.depth,1)
				cv.CvtColor( differenceImg, grayImg, cv.CV_RGB2GRAY )
				cv.Threshold( grayImg, grayImg, self._detectThresh, 255, cv.CV_THRESH_BINARY )
				contour = cv.FindContours( grayImg, cv.CreateMemStorage(0), cv.CV_RETR_EXTERNAL, cv.CV_CHAIN_APPROX_SIMPLE)	


				## draw bounding rect
				while contour:
					bounding_rect = cv.BoundingRect( list(contour) )
					area = bounding_rect[2]*bounding_rect[3]
					if area > self._minRectArea and area < self._maxRectArea and detect:
						videoGap = 0
						#print(str(area))
						if self._drawRect:
							self.drawBoundingRect(frame, bounding_rect)

					contour = contour.h_next()


				## write info to frame
				ms = "%04d" % int( (ts-int(ts)) * 10000 )
				t = time.strftime("%Y-%m-%d %H:%M:%S." + ms + " UTC", time.gmtime(ts))
				cv.PutText(frame, t, (5, frameSize[1] - 5), self._font, self._fontcolor)
				cv.PutText(frame, self._texttl, (5, 15), self._font, self._fontcolor)


				## save / show frame
				if videoGap < self._maxVideoGap:
					if newVideo:
						self.log("start capturing video " + t + ".mpg")
						newVideo = False

						directory = self._videoDir  + str(time.gmtime(ts).tm_year) \
							+ "/" + str("%02d" % time.gmtime(ts).tm_mon) + "/"

						if not self.isWriteable(directory):
							self._log(directory + "is not writeable!")
							self._run = False
							continue

						fileName = directory + str(self._thread) \
							+ "_" + (t.replace(" ", "_")).replace(":", "-") + ".mpg"

						videoWriter = cv.CreateVideoWriter(fileName, cv.CV_FOURCC('P','I','M','1'), 25, frameSize, 1)
						
						for img in historyBuffer.getImages():
							cv.WriteFrame(videoWriter, img)

					cv.WriteFrame(videoWriter, frame)
				else:
					if postFrames < self._postFrames and not newVideo:
						cv.WriteFrame(videoWriter, frame)
						postFrames += 1
					elif not newVideo:
						videoWriter = None
						self.log("stop capturing video " + t + ".mpg")
						postFrames = 0
						newVideo = True



				######## Add Frame to history buffer ########
				historyBuffer.add(cv.CloneImage( frame ))



				######## Window ########
				if self._showWindow:
					cv.ShowImage("Thread " + str(self._thread), frame)
					cv.WaitKey(40)

			else:
				self.log("no more frames (" + str(frameCount) +" frames)")
				break

		self.log("end detection thread " + str(self._thread))
		self.active = False



	######### test directory permission ##########	
	def isWriteable(self, dirname):
		
		if not os.path.exists(dirname):
			self.log(dirname + " does not exist...creating")
			os.makedirs(dirname)
			return True

		if not os.access(dirname, os.W_OK):
			self.log("no permission to write at " + dirname)
			return False
		
		return True


	######### draw bounding rect ##########	
	def drawBoundingRect(self, frame, bounding_rect):

		l = 10
		c = cv.CV_RGB(120,120,120)
		point1 = ( bounding_rect[0] - self._bRectOffset, bounding_rect[1] - self._bRectOffset )
		point2 = ( bounding_rect[0] - self._bRectOffset, bounding_rect[1] + bounding_rect[3] + self._bRectOffset )
		point3 = ( bounding_rect[0] + bounding_rect[2] + self._bRectOffset, bounding_rect[1] - self._bRectOffset )
		point4 = ( bounding_rect[0] + bounding_rect[2] + self._bRectOffset, bounding_rect[1] + bounding_rect[3] + self._bRectOffset)
		
		cv.Line(frame, point1, (point1[0] + l, point1[1]) , c)
		cv.Line(frame, point1, (point1[0], point1[1] + l) , c)

		cv.Line(frame, point2, (point2[0] + l, point2[1]) , c)
		cv.Line(frame, point2, (point2[0], point2[1] - l) , c)

		cv.Line(frame, point3, (point3[0] - l, point3[1]) , c)
		cv.Line(frame, point3, (point3[0], point3[1] + l) , c)

		cv.Line(frame, point4, (point4[0] - l, point4[1]) , c)
		cv.Line(frame, point4, (point4[0], point4[1] - l) , c)

		#cv.DrawContours(frame, contour, cv.CV_RGB(255,0,0), cv.CV_RGB(0,255,0), 0, 1, 0, (0,0) )
		#cv.Rectangle( frame, point1, point2, cv.CV_RGB(120,120,120), 1)

	######### Writes buffer to hdd ##########
	"""
	def saveVideo(self, videoBuffer, t, frameSize):

		self.log("write Buffer to disk")
		fileName = self._videoDir + (t.replace(" ", "_")).replace(":", "-") + ".mpg"
		videoWriter = cv.CreateVideoWriter(fileName, cv.CV_FOURCC('P','I','M','1'), 25, frameSize, 1)

		for img in videoBuffer.getImages():
			cv.WriteFrame(videoWriter, img)

		self.log("Buffer written to disk (" + str(videoBuffer.size()) + " frames)")
	"""

