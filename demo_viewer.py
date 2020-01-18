from __future__ import division
import time
import numpy as np
import cv2 
import argparse
import socket
from imagezmq import ImageHub
import subprocess
import os

def stop_cam(cam):
    """
    Stop the remote picamera systemd service.

    cam is the name of the remote camera host. Should match what is in ~/.ssh/config.
    """
    remote_command = f"ssh -f {cam} systemctl --user stop picamera@'\*'.service"
    print(remote_command)
    os.system(remote_command)
    

def start_cam(cam = 'pi1', host = ' ', port = ' '):
    """
    Start the remote picamera systemd service 

    cam is the name of the remote camera host. Should match what is in ~/.ssh/config.
  
    host is the network of this machine e.g. mymachine.local

    port is the port this machine will be listeing on.
    """
    try:
        # using systemd to manage daemons. {space} is for weird systemd escaping
        space = '\\\\x20'
        remote_command = f"ssh -f {cam} systemctl --user restart picamera@'{host}.local{space}{port}'" 
        print(remote_command)
        os.system(remote_command)
    except Exception as exc:
        sys.exit(f'SSH connection to {cam} failed with: {exc}')
    

def process_image(img):
    """
    Process image. Placeholder
    """

    orig_im = img
    # do something!
    img = cv2.Canny(img,100,200)
    return img, orig_im

def arg_parse():
    """
    Parse arguments.
    """
    
    parser = argparse.ArgumentParser(description='Remote picam demo')
   
    #TODO add arguments to control camera setting.
    
    return parser.parse_args()


if __name__ == '__main__':
    args = arg_parse()

    # EDIT THESE TO MATCH YOUR RASPBERRY PI NAMES
    camera_names = ['pi1', 'pi2' ]
    ports = dict.fromkeys(camera_names)
    thishost = socket.gethostname()
    for cam in camera_names: stop_cam(cam)
    
    print("Bind ports for cameras")
    font = cv2.FONT_HERSHEY_SIMPLEX
    hubs = {}
    port = 8222 # port for first camera
    for cam in camera_names:
        addr = socket.gethostbyname(f'{cam}.local')
        port_str = f'tcp://*:{port}'
        ports[cam] = port
        print(f'{thishost} waiting for {cam} at {port_str}')
        h = ImageHub(open_port=port_str)
        hubs[cam] = h
        # For each camera set up windows. "namedwindow" is resizable.
        cv2.namedWindow(f'{cam}a', cv2.WINDOW_NORMAL)
        cv2.namedWindow(f'{cam}b', cv2.WINDOW_NORMAL)
        port = port + 1 # next port

    for cam in camera_names:
        print(f'Send command to start {cam}')
        start_cam(cam = cam, host = thishost, port = ports[cam])
    print('Cameras starting')
    

try:
    start = time.time()
    frames = 0
    views = {}
    go = True
    while go:  
        # get frames nearly simultaneously
        for cam, h in hubs.items():
            #print(f'request image from {cam} {h}')
            msg, jpg_buffer = h.recv_jpg()
            frame = cv2.imdecode(np.frombuffer(jpg_buffer, dtype='uint8'), -1)
            #h.send_reply(b'OK') # tempting to do the mandatory reply here but don't. see below.
            views[cam] = (msg, frame)
            
        # process frames from cameras, single threaded for now
        for cam, (msg, frame) in views.items():
            
            img, orig_im = process_image(frame)
            #print(f'orig_im {type(orig_im)} {orig_im.shape}')
            #print(f'img {type(img)} {img.shape}')
            cv2.imshow(f'{cam}a', orig_im)
            cv2.imshow(f'{cam}b', img)
            
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                go = False
                break
            frames += 1
            # reset fps
            if frames == 20:
                now = time.time()
                try: fps = "{:5.1f}".format(frames / (now - start))
                except: fps = 0
                print(f'fps: {fps}')
                frames = 0
                start = time.time()

        for cam, h in hubs.items():
            # sending reply to camera enables next shot.
            # doing it at the end of processing on this end,
            # immediately before the next read means the streamer
            # won't build up a zmq message queue on the other end.
            # This prevents some frame syncing issues.
            h.send_reply(b'OK')
    
finally:
    print("Cleanup")
    cv2.destroyAllWindows()
    for cam in camera_names: stop_cam(cam)    
    print("Exiting")


    

    
    

