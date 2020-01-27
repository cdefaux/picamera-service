# picamera-service
This repo enables you to build a picamera streaming service that uses the local network to stream images from multiple Raspberry Pis with a Camera Module to a controlling computer. It includes a demo script that shows how to simultaneously process video from multiple picameras using the method. The goal here is to be able to start and stop multiple picams and collect images from all of them simultaneously, then process the images. It was designed for computer vision use cases, making it easy to swap out recorded video for your own live stream, for model query or for model learning. In these cases we don't care so much about maintaining a particular frame rate or smooth playback, we just want the most recent image from the picamera and the ability to process it remotely, on a box that is more powerful than the Raspberry Pi or a central hub for multiple cameras.

## Overview

The Raspberry Pi includes a slot for attaching the Camera Module. There are at least a couple of variations available for the Camera Module ([here][camera1] and [here][camera2]). These units use sensors identical to webcams, but are more directly connected to the processing capabilities of the Raspberry Pi. They are also a little cheaper than a USB webcam. The Raspberry Pi platform includes software for controlling the camera from the command line (raspistill, raspivid) and many tutorials sites (like [this one][commandline]) that can help you use them right away.

It is also also possible to use Python to access the picamera hardware. That's the direction taken in this repo. Docs are [here][picamera-docs] and there are many very nice tutorials on [pyimagesearch.com][pyimagesearch] that show how to write Python scripts to control the camera, access video and process images. 

Streaming video across the network is not directly supported by the Python libraries, so applications must pipe the camera output to programs that enable that, such as `mplayer`, `ffmpeg`, or `gstreamer`. These programs are widely used but are not so simple to manage. For one thing, they are opinionated about how to manage buffering for a video stream. Additionally, it is tricky to start and stop these programs from another program across the network without accidently creating zombie processes or failing to release camera access so it can be reacquired later. Lots of annoying rebooting ensues. 

You can find several repos that try to address this problem. One thing they have in common is the use of [Python wrapper][pyzmq] for the messaging library [Zeromq][zmq]. Here, we settled on [imagezmq][jeffbass] with minor modifications.

## Approach

The Raspberry Pi is an up-to-date linux plaform that includes systemd; the subsystem that starts, stops and restarts many standard linux services. We simply [set up a systemd service][systemd] for the camera and let systemd handle the start/stop/restarting of the camera. Then, `imagezmq` handles the connection and message passing between the camera and the receiving end. One tricky part is starting the camera service with an option that tells it where to send the images.`systemd` is not nicely designed to accept command line options, much less having them delivered over a remote `ssh` command. Hacking through multiple levels of string escaping solves the problem (see line 40 in `demo_viewer.py`, or even better, just look away). :-)

The demo script uses this approach to start the remote cameras, grab the images, process and politely shut them down on exit.

## Prerequisites

There a few dependencies not directly covered by the installation instructions below.

1. One or more Raspberry Pis with Camera Module installed.
2. The picamera units are already set up, with network configuration and Python3 already installed.
3. Importantly, you must be able to `ssh` into each Raspberry Pi without a password. Look [here][sshpi] if you are new to that. You will never go back. :-) 
4. Python dependencies are installed on all systems. If you use [nix](https://nixos.org), enter `nix-shell` to get a Python with dependencies. Otherwise, ensure you have Python3.6 or above, plus the following packages: imutils, numpy, opencv4.

## Installation

Install imagezmq. Currently this in not on PyPI, nor is the origianal repo pip-installable (as of 2020-01-22) so here's one way to get pip-installable version. 

````
$ cd picamera-service
$ git clone -b pip-installable git@github.com:timsears/imagezmq.git  
$ pip install imagezmq
````

````
$ git clone https://github.com/timsears/picamera-service.git
````

From here, we assume that there are one or more picamera units named `pi1`, `pi2`, etc. Do the steps for each camera as appropriate. Copy the repo to each picamera. Here's one way, for the first picamera, known to ssh as `pi1`...

````
$ scp -r picamera-service pi1:
````

Install the picamera service on each picamera. Here, for pi1...

````
$ ssh -f pi1 ./picamera-service/install.sh
````

## Running the service

The repo contains a Python script that provides an example of the service in use.

````
$ Python3 demo_viewer.py
````

You should see four windows pop up for the demo.


# Limitations / todos

The service does not yet permit remote camera configuration.

The service does not yet support webcams on the Raspberry Pi units.

### Acknowledgments:

Thanks to [TJ Sears](https://github.com/TJ-Sears) for important contributions and feedback on this project.


[camera1]: https://www.raspberrypi.org/products/camera-module-v2/
[camera2]: https://www.raspberrypi.org/products/pi-noir-camera-v2/
[commandline]: https://blog.robertelder.org/commands-raspberry-pi-camera/
[picamerdocs]: https://picamera.readthedocs.io
[pyimagesearch]: https://www.pyimagesearch.com
[systemd]: https://scruss.com/blog/2017/10/22/creating-a-systemd-user-service-on-your-raspberry-pi/
[jeffbass]: https://github.com/jeffbass/imagezmq
[pyzmq]: https://github.com/zeromq/pyzmq
[zmq]: https://zeromq.org
[sshpi]: https://www.raspberrypi.org/documentation/remote-access/ssh/
