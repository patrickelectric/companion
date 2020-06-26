#!/bin/bash
export COMPANION_DIR=$HOME/companion

cd $COMPANION_DIR/br-webui/

# limit logfile size to 10k lines
tail -n 10000 $HOME/.webui.log > /tmp/.webui.log
cp /tmp/.webui.log $HOME/.webui.log
rm -f /tmp/.webui.log

# start webserver
node index.js 2>&1 | tee -a $HOME/.webui.log
