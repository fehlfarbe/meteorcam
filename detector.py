#! /usr/bin/env python
#
#	gets images from video/device and detects
#	motions
#

import sys
import time
import cv2.cv as cv
import cv2
import imagestack
import thread
import os.path
import ConfigParser
import videocap as vc

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
		self._bin = 1
		self._gain = 10

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
				'fps' : self._fps,
				'bin' : self._bin,
				'gain' : self._gain
				}
		config = ConfigParser.RawConfigParser(defaults)
		config.read( configfile )
		
		## text
		self._fontsize = config.getfloat('DEFAULT', 'fontsize')
		self._fontcolor = config.get('DEFAULT', 'fontcolor')
		self._font = cv.InitFont(cv.CV_FONT_HERSHEY_DUPLEX, self._fontsize, self._fontsize, cv.CV_AA)
		self._texttl = config.get('DEFAULT', 'texttl')

		## motion detection
		self._deNoiseLevel = config.getint('DEFAULT', 'deNoiseLevel')
		self._darkframe = config.get('DEFAULT', 'darkframe')
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
		self._bin = config.getint('DEFAULT', 'bin')
		self._gain = config.getint('DEFAULT', 'gain')

		self.log("config loaded")

	######## Log ########
	def log(self, string):
		print("[%s] [%d]: %s" % (self._thread, time.time(), str(string)))
		#print("[" + str(self._thread) + "] " + str(string))


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
		### open cam ###
		cap = vc.VideoCapture(self._videoInput, self).capture
		if cap == None:
			self.log("Can't open camera!")
			self.active = False
			return
		
		cap.setFPS(self._fps)
		cap.setVideoSize(self._videoSize)
		cap.setBin(self._bin)
		cap.setGain(self._gain)
		
		
		### init ###
		frame, ts = cap.getFrame()
		
		if not frame:
			self.log("Error reading first frame")
			self.active = False
			return
		frameSize = cv.GetSize(frame)
		
		darkframe = None
		if self._darkframe:
			try:
				darkframe = cv.LoadImage(self._darkframe)
				if frameSize != cv.GetSize(darkframe):
					darkframe = None
					self.log("Darkframe has wrong size")
			except:
				self.log("Darkframe not found")
				
		mask = None
		'''
		if self._mask:
			try:
				tmp = cv.LoadImage(self._mask)
				mask = cv.CreateImage( frameSize, cv.IPL_DEPTH_8U, 1)
				cv.CvtColor( tmp, mask, cv.CV_RGB2GRAY )
				if frameSize != cv.GetSize(mask):
					raise Exception();
			except:
				self.log("Mask not found or wrong size")
		'''
		runAvg = cv.CreateImage( frameSize, cv.IPL_DEPTH_32F, frame.channels)
		runAvgDisplay = cv.CreateImage(frameSize, frame.depth, frame.channels)
		differenceImg = cv.CreateImage(frameSize, frame.depth, frame.channels)
		grayImg = cv.CreateImage(frameSize, cv.IPL_DEPTH_8U, 1)
		historyBuffer = imagestack.Imagestack(self._prevFrames)
		capbuf = None
		videoGap = self._maxVideoGap
		postFrames = 0
		frameCount = 1
		detect = False
		newVideo = True
		
		### testwindow
		if self._showWindow:
			self.log("Show window")
			cv.NamedWindow("Thread " + str(self._thread), 1)

		### capture loop ###
		while self._run:
			frame, ts = cap.getFrame()
			if ts == None:
				ts = time.time()
			
			videoGap += 1

			if frame:
				frameCount += 1

				if 1/float(frameCount) < self._avgLevel and not detect:
					self.log("start detection")
					detect = True
				
				### substract darkframe
				if darkframe:
					cv.Sub( frame, darkframe, frame )
	
				if self._deNoiseLevel > 0:
					cv.Smooth( frame, frame, cv.CV_MEDIAN, self._deNoiseLevel)
				cv.RunningAvg( frame, runAvg, self._avgLevel, mask )
				cv.ConvertScale( runAvg, runAvgDisplay, 1.0, 0.0 )
				cv.AbsDiff( frame, runAvgDisplay, differenceImg )
				
				if differenceImg.depth == grayImg.depth:
					grayImg = differenceImg
				else:
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
					
				#print "proctime: " + str(time.time()-ts)
				
				## write info to frame
				ms = "%04d" % int( (ts-int(ts)) * 10000 )
				t = time.strftime("%Y-%m-%d %H:%M:%S." + ms + " UTC", time.gmtime(ts))
				cv.PutText(frame, t, (5, frameSize[1] - 5), self._font, self._fontcolor)
				cv.PutText(frame, self._texttl, (5, 15), self._font, self._fontcolor)

				
				## save / show frame
				fname = "%s.png" % t
				if videoGap < self._maxVideoGap:
					if newVideo:
						self.log("Found motion, start capturing")
						capbuf = imagestack.Imagestack(self._prevFrames)
						newVideo = False						
						directory = os.path.join(self._videoDir,
											"%d/%02d/%s" % (time.gmtime(ts).tm_year, time.gmtime(ts).tm_mon, t))

						if not self.isWriteable(directory):
							self._log(directory + "is not writeable!")
							self._run = False
							continue

						#for img in historyBuffer.getImages():
						#	cv.SaveImage(os.path.join(directory, "%s.png" % img['time']), img['img'])
						capbuf.addList(historyBuffer.getImages())

					#cv.SaveImage(os.path.join(directory, fname), frame)
					capbuf.add(frame, t)
				else:
					if postFrames < self._postFrames and not newVideo:
						#cv.SaveImage(os.path.join(directory, fname), frame)
						capbuf.add(frame, t)
						postFrames += 1
					elif not newVideo:
						self.log("Stop capturing")
						### write images to hdd in new thread ###
						thread.start_new(self.saveVideo, (directory, capbuf))
						#self.saveVideo(directory, capbuf)
						capbuf = None
						postFrames = 0
						newVideo = True



				######## Add Frame to history buffer ########
				historyBuffer.add(cv.CloneImage( frame ), t)



				######## Window ########
				if self._showWindow:
					cv.ShowImage("Thread " + str(self._thread), frame)
					cv.ShowImage("Thread %d avg" % self._thread, runAvgDisplay)
					cv.ShowImage("Thread %d diff" % self._thread, differenceImg)
					cv.WaitKey(1)
				
				self.log("Proc: " + str(time.time() - ts))

			else:
				self.log("no more frames (" + str(frameCount) +" frames)")
				break

		self.log("Close camera")
		cap.close()
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
		c = cv.CV_RGB(200,120,120)
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
	def saveVideo(self, dir, videoBuffer):
		self.log("Write captured images to %s" % dir)
		
		for img in videoBuffer.getImages():
			cv.SaveImage(os.path.join(dir, "%s.png" % img['time']), img['img'])
			
		self.log("Images written to %s" % dir)
		
	"""
	def saveVideo(self, videoBuffer, t, frameSize):

		self.log("write Buffer to disk")
		fileName = self._videoDir + (t.replace(" ", "_")).replace(":", "-") + ".mpg"
		videoWriter = cv.CreateVideoWriter(fileName, cv.CV_FOURCC('P','I','M','1'), 25, frameSize, 1)

		for img in videoBuffer.getImages():
			cv.WriteFrame(videoWriter, img)

		self.log("Buffer written to disk (" + str(videoBuffer.size()) + " frames)")
	"""

