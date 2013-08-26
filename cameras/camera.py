'''
Created on 25.08.2013

@author: kolbe
'''

class camera(object):
    '''
    classdocs
    '''


    def __init__(self):
        
        self._fps = 0
        self._exp = 1
        self._gain = 0
        self._bin = 1
        self._videoSize = (0,0)
        
    def setBin(self, b):
        self._bin = b
        
    def setFPS(self, fps):
        self._fps = fps
        
        ### exposure time in ms
        self._exp = int(1/float(self._fps)*1000)
        #print self._exp
        
    def setVideoSize(self, size):
        self._videoSize = size
    
    def getFrame(self):
        return None
    
    def close(self):
        pass
        