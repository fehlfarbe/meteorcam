'''
Created on 15.09.2013

@author: kolbe
'''

from flask import Flask, render_template, request, abort, json, jsonify, make_response, redirect, url_for, Response, send_file
import threading, time
from PIL import Image
import StringIO
import cv2.cv as cv

class httpserver:
    
    def __init__(self, port = 8000):

        self._image = None
        self.t1 = threading.Thread(target=self.startServer, args=(port,))
        self.t1.daemon = True
        self.t1.start()
        
        self._lock = False
        
    
    def startServer(self, port):
        app = Flask(__name__)

        @app.route('/')
        def index():
            self._lock = True
            pimg = Image.fromstring("L", cv.GetSize(self._image), self._image.tostring())
            self._lock = False
            
            img_io = StringIO.StringIO()
            pimg.save(img_io, 'JPEG', quality=100)
            img_io.seek(0)
            
            return send_file(img_io, mimetype='image/jpeg')
        
        #app.run(host="0.0.0.0", port = port, debug=True, use_reloader=False)
        app.run(host="0.0.0.0", port = port, debug=True, use_reloader=False)
    
    def shutdown(self):
        pass
    def updateImage(self, image):
        if self._lock:
            return
        self._image = image