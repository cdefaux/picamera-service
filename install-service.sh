#!/bin/sh
mkdir -p ~/.config/systemd/user/
ln -sf $(pwd)/picamera@.service ~/.config/systemd/user/
systemctl --user enable picamera@.service
