#!/usr/bin/env python3

'''
Simple script to connect to a Phoenix Inverter and fetch some data
Requires a BT-dongle

This device requires to be paired to work.  Default pin = "000000"
This is only needed the first time you connect to a device

The easiest way to do that is to run 

$ bluetootctl
[bluetooth]# scan on
(...)
[bluetooth]# scan off
[bluetooth]# devices
(...)
Device DE:33:11:25:xx:xx VE.Direct Smart
(...)
[bluetooth]# connect DE:33:11:25:xx:xx
Attempting to connect to DE:33:11:25:xx:xx
Connection successful

[VE.Direct Smart]# trust 
Changing DE:33:11:25:xx:xx trust succeeded

[VE.Direct Smart]# pair
Attempting to pair with DE:33:11:25:xx:xx
Request passkey
[agent] Enter passkey (number in 0-999999): 000000
Pairing successful
[VE.Direct Smart]# 

You can then exit from bluetoothctl

Or you can use "menu gatt" and start looking at the different characteristics, and enable notifications for them to see what happens




'''

import gatt
import time
import threading
from datetime import datetime, timedelta

#  Set to your BT-dongles MAC-address
mac_address = "DE:33:11:25:xx:xx"

device_manager = gatt.DeviceManager(adapter_name="hci0")
device_manager.update_devices()

# device_manager.start_discovery()
# time.sleep(5)
# device_manager.stop_discovery()




charactersistcs = {}


class PhoenixDevice(gatt.Device):
    def __init__(self, mac_address, manager):
        super().__init__(mac_address=mac_address, manager=manager)
        self.last_notify = datetime.now() + timedelta(seconds=10)
        self.char_buffer = {}
    def characteristic_enable_notifications_succeeded(self, characteristic,):
        print("[{}] Notifications enabled...".format(characteristic.uuid))

    def characteristic_enable_notifications_failed(self, characteristic, error):
        print("[{}] Notifications not enabled {}".format(characteristic.uuid, error))


    def characteristic_value_updated(self, characteristic, value):
        self.last_notify = datetime.now() 
        if characteristic.uuid == "306b0004-b081-4037-83dc-e59fcc3cdfd0":
            print("[{}] Changed to {}".format(characteristic.uuid, value))
            self.getBulkValue(characteristic.uuid, value)
        elif characteristic.uuid == "306b0003-b081-4037-83dc-e59fcc3cdfd0":
            pass
        else:
            print("[{}] Changed to {}".format(characteristic.uuid, value))
            self.getValue(characteristic.uuid, value)
        

    def getBulkValue(self, char, value):
        start = int.from_bytes(value[0:2], byteorder="little")
        if start == 776:
            self.char_buffer[char] = value
        else:
            self.char_buffer[char] = self.char_buffer[char] + value[:]
        if len(self.char_buffer[char]) > 20:
            i = 0
            while i + 8 <= len(self.char_buffer[char]):
                val = self.char_buffer[char][i:i+8]
                self.getValue(char, val)
                i = i + 8

#   08 03 19 22 00 42 dc 59 
#   08 03 19 22 00 42 d9 59 
#   08 03 19 22 00 42 dc 59 
#   08 03 19 ed 8d 42 35 05 
#   08 03 19 ed 8d 42 34 05                                      


    def setPowerSwitch(self, characteristic, state):
        val = None
        print ("Setting power switch to {}".format(state))
        if state == "on":
            val = " 0603821902004102"
        if state == "off":
            val = "0603821902004104"
        if state == "eco":
            val = "0603821902004105"
        if val:
            b  = bytearray.fromhex(val)
            characteristic.write_value(b)



    def getValue(self, char, value):

        if len(value) == 8:
            packet3 = value[3]
            packet4 = value[4]
            packet6 = value[6]
            packet7 = value[7]
            ptype = int.from_bytes(value[3:5], byteorder="little")
            pval  = int.from_bytes(value[6:8], byteorder="little")
            if ptype == 34:
                print("Output voltage: {} V".format(pval * 0.01))
            elif ptype == 36333:
                print("Input voltage: {} V".format(pval * 0.01))
            elif ptype == 290:
                if pval == 0:
                    print("Output Power turned off")
                elif pval == 65534:
                    print("Output Power turned on")
                else:
                    print("Current: {} A".format(pval * 0.1))
            else:
                print("?? {}: {}".format(ptype, pval))
                print("P3 {}, P4 {}, P6 {}, P7 {}".format(packet3, packet4, packet6, packet7))
        if len(value) == 7:
            # Probably power?
            # 08 03 19 02 00 41 05 
            ptype = int(str(value[4]), 16)
            pval  = int(str(value[6]), 16)
            state = "?"
            if ptype == 0:
                if pval == 2:
                    state = "on"
                if pval == 4:
                    state = "off"
                if pval == 5:
                    state = "eco"
                print("PowerSwitch - {} Type: {} Value {}".format(state, ptype, pval))
            if ptype == 1:
                if pval == 0:
                    state = "off"
                if pval == 1:
                    state = "eco"
                if pval == 9:
                    state = "on"
                print("PowerState - {} Type: {} Value {}".format(state, ptype, pval))
            # if packet3 == 34 and packet4 == 0

device = PhoenixDevice(mac_address=mac_address, manager=device_manager)

device.connect()
time.sleep(5)

logger_name = "x"



for service in device.services:
    print("[{}]  Service [{}]".format(logger_name, service.uuid))
    # if service_notify and service.uuid == service_notify:
    #    print("[{}]  - Found dev notify service [{}]".format(logger_name, service.uuid))
    #     device_notification_service = service
    # if service_write and service.uuid == service_write:
    #     print("[{}]  - Found dev write service [{}]".format(logger_name, service.uuid))
    #     device_write_service = service
    for characteristic in service.characteristics:
        print("[{}]    Characteristic [{}]".format(logger_name, characteristic.uuid))
        if service.uuid == "306b0001-b081-4037-83dc-e59fcc3cdfd0":
            print("[{}]    - {} Enabling notifications".format(logger_name, characteristic.uuid))
            characteristic.enable_notifications()
            charactersistcs[characteristic.uuid] = characteristic

char_ids = {
    '0020': "306b0002-b081-4037-83dc-e59fcc3cdfd0",
    '0023': "306b0003-b081-4037-83dc-e59fcc3cdfd0",
    '0026': "306b0004-b081-4037-83dc-e59fcc3cdfd0",
}

#
# This is just fetched from a packet dump when using the app
# I am not sure all of this is necessary, and what the commands 
# actually do...
# But it works
#


c = charactersistcs["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
hs = "fa80ff"
b  = bytearray.fromhex(hs)
c.write_value(b);

hs = "f980"
b  = bytearray.fromhex(hs)
c.write_value(b);

hs = "01"
b  = bytearray.fromhex(hs)
c.write_value(b);

c = charactersistcs["306b0003-b081-4037-83dc-e59fcc3cdfd0"]

hs = "01"
b  = bytearray.fromhex(hs)
c.write_value(b);

hs = "0300"
b  = bytearray.fromhex(hs)
c.write_value(b);

hs = "060082189342102703010303"
b  = bytearray.fromhex(hs)
c.write_value(b);

c = charactersistcs["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
hs = "f941"
b  = bytearray.fromhex(hs)
c.write_value(b);


def device_poller():
    i = 0
    while (1): 
        # Just a simple loop to send different commands towards the device
        time.sleep(1)
        if device.last_notify < datetime.now() - timedelta(seconds=10):
            # Seems like I need to send this from time to time to keep the 
            # notification flowing.  If I don't they stop after everything form
            # a few seconds to a couple of minutes
            print("Sending push for refreshed data")
            c = charactersistcs["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
            hs = "f941"
            b  = bytearray.fromhex(hs)
            c.write_value(b);

        # Just testing how to turn the power on/off/eco and watching what happens
        if i == 20:
            c = charactersistcs["306b0003-b081-4037-83dc-e59fcc3cdfd0"]
            device.setPowerSwitch(c, "eco")
            time.sleep(1)
            c = charactersistcs["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
            hs = "f941"
            b  = bytearray.fromhex(hs)
            c.write_value(b);
        if i == 50:
            c = charactersistcs["306b0003-b081-4037-83dc-e59fcc3cdfd0"]
            device.setPowerSwitch(c, "on")
            time.sleep(1)
            c = charactersistcs["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
            hs = "f941"
            b  = bytearray.fromhex(hs)
            c.write_value(b);
        if i == 70:
            c = charactersistcs["306b0003-b081-4037-83dc-e59fcc3cdfd0"]
            device.setPowerSwitch(c, "off")
            time.sleep(1)
            c = charactersistcs["306b0002-b081-4037-83dc-e59fcc3cdfd0"]
            hs = "f941"
            b  = bytearray.fromhex(hs)
            c.write_value(b);
        if i == 100:
            i = 0
        i = i + 1

t1 = threading.Thread(target=device_poller)
t1.daemon = True 
t1.start()

device_manager.run()


# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x08\x03\x19"\x00B\xd9Y\x08\x03\x19"\x00B\xdaY\x08\x03\x19"'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x08\x03\x19"\x00B\xd9Y\x08\x03\x19"\x00B\xdaY\x08\x03\x19"'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x00B\xdfY\x08\x03\x19"\x00B\xdaY\x08\x03\x19"\x00B\xd9Y'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x00B\xdfY\x08\x03\x19"\x00B\xdaY\x08\x03\x19"\x00B\xd9Y'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x08\x03\x19"\x00B\xdaY\x08\x03\x19\xed\x8dB\x16\x05\x08\x03\x19"'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x08\x03\x19"\x00B\xdaY\x08\x03\x19\xed\x8dB\x16\x05\x08\x03\x19"'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x00B\xd9Y\x08\x03\x19"\x00B\xdaY\x08\x03\x19"\x00B\xd9Y'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x00B\xd9Y\x08\x03\x19"\x00B\xdaY\x08\x03\x19"\x00B\xd9Y'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x08\x03\x19"\x00B\xdaY\x08\x03\x19"\x00B\xd9Y\x08\x03\x19"'
# [306b0004-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x08\x03\x19"\x00B\xdaY\x08\x03\x19"\x00B\xd9Y\x08\x03\x19"'
# [306b0003-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x00B\xdfY\x08\x03\x19"\x00B\xdaY'
# [306b0003-b081-4037-83dc-e59fcc3cdfd0] Changed to b'\x00B\xdfY\x08\x03\x19"\x00B\xdaY'

# bluetoothctl

# select-attribute /org/bluez/hci0/dev_DE_33_11_25_72_13/service001f/char0020
# write "0xfa 0x80 0xff"
# write "0xf9 0x80"
# write "0x01"
# select-attribute /org/bluez/hci0/dev_DE_33_11_25_72_13/service001f/char0023
# write "0x01"
# write "0x03 0x00"
# write "0x06 0x00 0x82 0x18 0x93 0x42 0x10 0x27 0x03 0x01 0x03 0x03"





