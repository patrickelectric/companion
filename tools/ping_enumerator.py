#!/usr/bin/env python -u

"""Scan serial ports for ping devices
    Symlinks to detected devices are created under /dev/serial/ping/
    This script needs root permission to create the symlinks
"""
from __future__ import print_function
import subprocess
from brping import PingDevice
from brping.definitions import *
import serial
import time

class PingEnumerator:

    def legacy_detect_ping1d(self, ping):
        """
        Detects Ping1D devices without DEVICE_INFORMATION implemented
        """
        firmware_version = ping.request(PING1D_FIRMWARE_VERSION)
        if firmware_version is None:
            return None
        description = "/dev/serial/ping/Ping1D-id-%s-t-%s-m-%s-v-%s.%s" % (
            firmware_version.src_device_id,
            firmware_version.device_type,
            firmware_version.device_model,
            firmware_version.firmware_version_major,
            firmware_version.firmware_version_minor
        )
        return description

    def detect_device(self, dev):
        """
        Attempts to detect the Ping device attached to serial port 'dev'
        Returns the new path with encoded name if detected, or None if the
        device was not detected
        """

        try:
            ping = PingDevice("/dev/serial/by-id/" + dev, 115200)
        except Exception as exception:
            print("An exception has occurred: ", exception)
            return None

        if not ping.initialize():
            return None

        device_info = ping.request(COMMON_DEVICE_INFORMATION)
        if not device_info:
            return self.legacy_detect_ping1d(ping)

        if device_info.device_type == 1:
            description = "/dev/serial/ping/Ping1D-id-%s-r-%s-v-%s.%s.%s"
        elif device_info.device_type == 2:
            description = "/dev/serial/ping/Ping360-id-%s-r-%s-v-%s.%s.%s"
            # Open device with 2M baud to setup Ping360
            print("Setting baud to 2M...")
            ser = serial.Serial("/dev/serial/by-id/" + dev, 2000000)
            ser.send_break()
            ser.write("UUUUUUU".encode())
            ser.close()
            self.set_low_latency(dev)

        else:
            return None

        return description % (
            device_info.src_device_id,
            device_info.device_revision,
            device_info.firmware_version_major,
            device_info.firmware_version_minor,
            device_info.firmware_version_patch
        )

    def set_low_latency(self, dev):
        """
        Receives /dev/serial/by-id/...
        maps to it to ttyUSB and sets the latency_timer for the device
        """
        target_device = subprocess.check_output(' '.join(["readlink", "-f", "/dev/serial/by-id/%s" % dev]), shell=True)
        device_name = target_device.decode().strip().split("/")[-1]

        latency_file = "/sys/bus/usb-serial/devices/{0}/latency_timer".format(device_name)

        with open(latency_file, 'w') as p:
            p.write("1")
            p.flush()

    def make_symlink(self, origin, target):
        """
        follows target to real device an links origin to it
        origin => target
        Returns True if sucessful
        """
        try:
            # Follow link to actual device
            target_device = subprocess.check_output(' '.join(["readlink", "-f", "/dev/serial/by-id/%s" % origin]), shell=True)
            # Strip newline from output
            target_device = target_device.decode().split('\n')[0]

            # Create another link to it
            subprocess.check_output(' '.join(["mkdir", "-p", "/dev/serial/ping"]), shell=True)
            subprocess.check_output("ln -fs %s %s" % (
                target_device,
                target), shell=True)
            print(origin, " linked to ", target)
            return True
        except subprocess.CalledProcessError as exception:
            print(exception)
            return False


    def erase_old_symlinks(self):
        """
        Erases all symlinks at "/dev/serial/ping/"
        """
        try:
            subprocess.check_output(["rm", "-rf", "/dev/serial/ping"])
        except subprocess.CalledProcessError as exception:
            print(exception)


    def list_serial_devices(self):
        """
        Lists serial devices at "/dev/serial/by-id/"
        """
        # Look for connected serial devices
        try:
            output = subprocess.check_output("ls /dev/serial/by-id", shell=True)
            return output.decode().strip().split("\n")
        except subprocess.CalledProcessError as exception:
            print(exception)
            return []




if __name__ == '__main__':
    enumerator = PingEnumerator()
    enumerator.erase_old_symlinks()

    # Look at each serial device, probe for ping
    for dev in enumerator.list_serial_devices():
        link = enumerator.detect_device(dev)
        if link:
            enumerator.make_symlink(dev, link)
        else:
            print("Unable to identify device at ", dev)
