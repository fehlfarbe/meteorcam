'''
Created on 25.08.2013

@author: kolbe
'''
import cv2.cv as cv
import cameras.qhy5 as qhy5
import cameras.ocvcam as ocvcam

class VideoCapture(object):
    '''
    classdocs
    '''

    def __init__(self, videoIn, parent):
    
        self._parent = parent;
        self.capture = None
        
        if videoIn == "QHY5":
            self.capture = qhy5.qhy5()
        else:
            self.capture = ocvcam(videoIn)