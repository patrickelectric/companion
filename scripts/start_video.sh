#!/bin/bash

# Load Pi camera v4l2 driver
sudo modprobe bcm2835-v4l2

if [ -z "$4" ]; then

  echo 'No device specification'
  if lsusb | grep 05a3:9422; then
    echo "USB Cam"
    DEVICE="/dev/video1"
  else
    echo "Raspi Cam"
    DEVICE="/dev/video0"
  fi

else
  DEVICE=$4
fi

gstOptions=$(tr '\n' ' ' < /home/pi/gstreamer2.param)

echo "starting device $DEVICE with width $1 height $2 framerate $3 options $gstOptions"

screen -X -S video quit
screen -dm -S video bash -c "export LD_LIBRARY_PATH=/usr/local/lib/ && gst-launch-1.0 -ev v4l2src device=$DEVICE do-timestamp=true ! video/x-h264, width=$1, height=$2, framerate=$3/1 $gstOptions"
