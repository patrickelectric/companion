#!/bin/bash
export LD_LIBRARY_PATH=/usr/local/lib/

# Load Pi camera v4l2 driver
if ! lsmod | grep bcm2835_v4l2; then
    sudo modprobe bcm2835-v4l2
fi

screen -X -S video quit

DEVICE=$4

gst-launch-1.0 v4l2src device=$DEVICE do-timestamp=true ! video/x-h264 ! h264parse ! queue ! rtph264pay config-interval=10 pt=96 ! fakesink num-buffers=1

if [ $? != 0 ]; then
    echo "specified device $DEVICE failed"
    for DEVICE in $(ls /dev/video*); do
        echo "attempting to start $DEVICE"
        gst-launch-1.0 v4l2src device=$DEVICE do-timestamp=true ! video/x-h264 ! h264parse ! queue ! rtph264pay config-interval=10 pt=96 ! fakesink num-buffers=1
        if [ $? == 0 ]; then
            echo "Success!"
            break
        fi
    done
fi

gstOptions=$(tr '\n' ' ' < /home/pi/gstreamer2.param)

echo "starting device $DEVICE with width $1 height $2 framerate $3 options $gstOptions"
echo $1 > ~/vidformat.param
echo $2 >> ~/vidformat.param
echo $3 >> ~/vidformat.param
echo $DEVICE >> ~/vidformat.param

screen -dm -S video bash -c "export LD_LIBRARY_PATH=/usr/local/lib/ && gst-launch-1.0 -v v4l2src device=$DEVICE do-timestamp=true ! video/x-h264, width=$1, height=$2, framerate=$3/1 $gstOptions"
