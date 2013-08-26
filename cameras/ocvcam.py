'''
Created on 26.08.2013

@author: kolbe
'''
import camera
import cv2.cv as cv
import time

class ocvcam(camera.camera):
    '''
    classdocs
    '''


    def __init__(self, videoIn):
        try:
            self._capture = cv.CaptureFromCAM(int(videoIn))
        except:
            self._capture = cv.CaptureFromFile(videoIn)
        
    
#     def setBin(self, b):
#         self._bin = b
        
    def setFPS(self, fps):
        super(ocvcam, self).setFPS(fps)
        cv.SetCaptureProperty(self._capture, cv.CV_CAP_PROP_FPS, fps)
        
    def setVideoSize(self, size):
        super(ocvcam, self).setVideoSize(size)
        cv.SetCaptureProperty(self._capture, cv.CV_CAP_PROP_FRAME_WIDTH, self._videoSize[0])
        cv.SetCaptureProperty(self._capture, cv.CV_CAP_PROP_FRAME_HEIGHT, self._videoSize[1])
    
    def getFrame(self):
        return cv.QueryFrame(self._capture), time.time()