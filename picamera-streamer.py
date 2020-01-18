"""
A streaming program imagezmq to send image frames from the PiCamera continuously to a receiving program elsewhere that will process the 
images as a video stream.

It can be run from the command line (good for testing) but is intended to be run as a daemon. 

This program requires that the image receiving program be running first. After starting an ImageHub instance, the receving program should issue a command to pi to (re)start the daemon.  

Passing arguments to a systemd daemon is possible but a little tricky.

TODO: Add how to set up the service

Some useful commands... 

Stop service (matches all the command line variations that may be running
sudo systemctl stop picamera@'*'.service

Start / restart with defaults (just exits):
`sudo systemctl start "picamera@\x20.service"`
`sudo systemctl restart "picamera@\x20.service"`

Start / restart with args:
`sudo systemctl start picamera@'festuca.local 8234'.service`
`sudo systemctl restart picamera@'festuca.local 8234'.service`

This avoids a escaping warning and results in the same argv for python:
sudo systemctl restart picamera@festuca.local\\x208234.service

"""

import sys

import socket
import time
import cv2
from imutils.video import VideoStream
import imagezmq
import argparse
import socket
import itertools

# primitive arg parsing thanks to finicky systemd requirements

print(f'args: {sys.argv}')
viewer_name, viewer_port = sys.argv[1].split(' ')

if viewer_name is '': exit(0) # no args? just die

picam = VideoStream(usePiCamera=True, resolution=(1200, 1200)).start()

cam_name = socket.gethostname()

print(f'Starting Picamera on {cam_name}')
viewer_ip = socket.gethostbyname(viewer_name)
viewer_addr = f'tcp://{viewer_ip}:{viewer_port}'
viewer = imagezmq.ImageSender(connect_to = f'tcp://{viewer_ip}:{viewer_port}')
print(f'Ready to send to {viewer_name} at {viewer_addr}')

jpeg_quality = 98  # 0 to 100, higher is better quality, 95 is cv2 default
while True:  # send images as stream until Ctrl-C
    image = picam.read()
    ret_code, jpg_buffer = cv2.imencode(
        ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
    viewer.send_jpg(cam_name, jpg_buffer)



