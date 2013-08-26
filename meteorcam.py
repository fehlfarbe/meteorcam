#! /usr/bin/env python
#
#	gets images from video/device and detects
#	motions
#

import detector
import sys
import thread
import os
import signal

threads = []

def exit_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        for thread in threads:        
            thread.stop()

if __name__ == "__main__":
    threadFiles = os.listdir("threads/")
    tnr = 0
    
    for fname in threadFiles:
        if os.path.isfile("threads/"+fname):
            t = detector.Detector(tnr, "./config.conf")
            t.start("threads/"+fname)
            threads.append(t)
            tnr += 1
    
    active = True
    signal.signal(signal.SIGINT, exit_handler)
    
    while active:
        active = False
        for thread in threads:		
            if thread.active:
                active = True
    
    print("Close meteorcam")
    sys.exit(0)
    print("Closed")