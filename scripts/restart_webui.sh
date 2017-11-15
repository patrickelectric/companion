#!/bin/bash

export COMPANION_DIR=/home/pi/companion

screen -X -S webui quit
cd /home/pi/companion/br-webui
node index.js