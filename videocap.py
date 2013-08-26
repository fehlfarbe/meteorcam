'''
Created on 25.08.2013

@author: kolbe
'''
import cv2.cv as cv
import cameras.camera as camera
import cameras.qhy5 as qhy5


class VideoCapture(object):
    '''
    classdocs
    '''

    def __init__(self, videoIn, parent):
    
        self._parent = parent;
        self._capture = None
        
        if videoIn == "QHY5":
            self._capture = qhy5.qhy5()
        else:
            try:
                self._capture = cv.CaptureFromCAM(int(videoIn))
                parent.log("Capture from cam")        
            except:
                self._capture = cv.CaptureFromFile(videoIn)
                parent.log("Capture from file " + videoIn)
        
        #print self._capture

    
    def setFPS(self, fps):
        if isinstance(self._capture, camera.camera):
            self._capture.setFPS(fps)
        else:
            cv.SetCaptureProperty(self._capture, cv.CV_CAP_PROP_FPS, fps)
        
    def setSize(self, videoSize):
        if isinstance(self._capture, camera.camera):
            self._capture.setVideoSize(videoSize)
        else:
            cv.SetCaptureProperty(self._capture, cv.CV_CAP_PROP_FRAME_WIDTH, videoSize[0])
            cv.SetCaptureProperty(self._capture, cv.CV_CAP_PROP_FRAME_HEIGHT, videoSize[1])
        
    def getFrame(self):
        if isinstance(self._capture, camera.camera):
            return self._capture.getFrame()
        else:
            return cv.QueryFrame(self._capture)
        
    def setBin(self, b):
        if isinstance(self._capture, camera.camera):
            self._capture.setBin(b)
        else:
            self._parent.log("Binning not supported!")
            
    def closeCam(self):
        if isinstance(self._capture, camera.camera):
            self._capture.close()