'''
Created on 25.08.2013

@author: kolbe
'''
import camera
import ctypes
from ctypes import cdll
import cv2.cv as cv
import numpy as np
import os
import time


class qhy5(camera.camera):
    '''
    classdocs
    '''


    def __init__(self):
        lib = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), 'libqhy5lib.so'))
        self._cap = lib.capture
        self._setVal = lib.setValues
        self._opencam = lib.openCamera
        self._closecam = lib.closeCamera
        self._cap.restype = ctypes.c_char_p

     
        self._gain = 10
        self._bin = 1
        self._exp = 100
        
        self._opencam()
        self._setVal(self._exp, self._gain, self._bin)
        
        
    def setBin(self, b):        
        if b in range(0,4):
            self._bin = b
        else:
            print( "Binning value not between 0 and 4 (value %d)" % b)
            
        self._setVal(self._exp, self._gain, self._bin)
        
    def setFPS(self, fps):
        super(qhy5, self).setFPS(fps)
        self._setVal(self._exp, self._gain, self._bin)
        
    def setGain(self, g):
        self._gain = g
        self._setVal(self._exp, self._gain, self._bin)
    
    def getFrame(self):
        #t = time.time()
        buf = self._cap()

        mat = cv.CreateImageHeader( (1280 / self._bin, 1024 / self._bin), cv.IPL_DEPTH_8U, 1)
        cv.SetData(mat, buf, cv.CV_AUTOSTEP)
        #print time.time()-t
        return mat
    
    def setVideoSize(self, size):
        print("setVideoSize not supported for QHY5! Use bin instead!")
        
    def close(self):
        self._closecam()