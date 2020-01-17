#!/bin/bash
# Check if a navigator hat is connected
# Return code is equal to version of the board, zero when no board is detected

# Look for PCA9685 (0x40) and ADS1115 (0x48) respectively
# Use i2cdump to detect the first register of the sensor address
# And check if it's a valid read
i2cdump -y -r 0x00-0x01 1 0x40 | grep -v XX | grep 00:
PCA9685_DETECTED=$?

i2cdump -y -r 0x00-0x01 1 0x48 | grep -v XX | grep 00:
ADS115_DETECTED=$?

if [ $PCA9685_DETECTED != 0 ] || [ $ADS115_DETECTED != 0 ]; then
    echo "Navigator not detected."
    return 0
else
    echo "Navigator detected."
    return 1
fi
