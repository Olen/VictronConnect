# VictronConnect
<img src="https://github.com/Olen/VictronConnect/blob/master/VictronConnect.png?raw=true">

## This repository is in no way approved by or afiliated with the official Victron Energy repository.  
This is just my private take at understanding the protocol used by VictronConnect Bluetooth.

If you use the information here to connect to your device and it breaks, you are allowed to keep the pieces.

## Decompiling the VictronConnect app

These are some useful files when trying to decompile the VictronConnect to talk to VE Direct appliances.

*data-structures.json* is a dump of what data you can expect to read/set for most of the available VC devices.  It is NOT valid json, so if you want to use some of the data, you probably need to modify it to fit your need.

*devices.xml* is a huge XML file with various information about the devices. This file also has readable names for the devices so you can search for them there

Each device in devices.xml has a section like this:
```
    <model>
        <description>Phoenix Inverter 12V 800VA 230Vac</description>
        <id>41569</id>
    </model>
```
By converting the id field to hex: 41569 => 0xA261 you can find the device in "data-structures.json"
```
  "productid":"0xA261",
```
That data dump is not very well structured, so the information you look for might be either just above or just below the "productid"

*phoenix.py* is a simple script to connect to an inverter and read some data.  Might be used as a starting point if you want to test the same for another device


## Background

For some reason, Victron Energy has decided that they want to be open with all their protocols _except_ Bluetooth.
They have an extensive github repo here: https://github.com/victronenergy

And their software is available here: https://www.victronenergy.com/support-and-downloads/software
- including the VictronConnect app

Documentation of their open protocols and APIs is here: https://www.victronenergy.com/upload/documents/Whitepaper-Data-communication-with-Victron-Energy-products_EN.pdf

But their only "FAQ"-question on this page: https://www.victronenergy.com/live/open_source:start is quite disappointing:

### Q1. Why is the Bluetooth API not public?
> Making the bluetooth API an official public one would mean that we can’t change it as simply as we can today; and also it means that we’ll get questions about it: bluetooth is not simple. Far more complicated than a serial port.
> 
> And then only our developers will be able to answer them: taking away development resources. Hence we chose to not make the Bluetooth API public.

So that is why I started reverse engineering the protocol, as I wanted to be able to monitor a couple of VE devices over bluetooth.  It is silly to be forced to use a serial port when BT is available and works fine without cabling.

Currently the script *phoenix.py* is able to connect to a Phoenix inverter, and read the most relevant data
- Input Voltage
- Output Voltage
- Current

In addition to being able to switch power between "on", "off" and "eco".


## Helping

If you want to help, the easiest is to download the VictronConnect app for Linux (or Mac, I guess) and run wireshark to catch what packes are sent over the bluetooth connection when the app monitors and manages your device.

Do not hesitate to contact me if you need help in decoding the PCAP-file that is captured.


### bluetoothctl
Another nice way to snoop on what is going on after you have figured out the correct UUIDs is to run bluetoothctl

* Connect to the device and go into "menu gatt"
* Use "list-attributes" to find the different charactersticts.
* Select an interesting attribute and enable notifications


```
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
[VE.Direct Smart]# menu gatt
[VE.Direct Smart]# list-attributes 
(...)
[VE.Direct Smart]# select-attribute 306b0003-b081-4037-83dc-e59fcc3cdfd0
[VE.Direct Smart:/service001f/char0023]# notify on
Notify started

```

You can then see what happens while your computer connects to the device.  Be aware that you can not do this while running the app on another device, as BLE only allows one connected device at the time. So you will not be able to connect to the VE device with both your phone and your computer at the same time.  But you CAN do this while running the Victron Connect app on your computer.


### Android
To do a packet capture from Android, download the nRF Connect and Logger apps: 
* https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp
* https://play.google.com/store/apps/details?id=no.nordicsemi.android.log

Keep nRF Logging enabled while you run the VictronConnect app on your phone and save the logs somewhere after you have done a few operations.

Alternatively, enable developer options in Android

https://www.digitaltrends.com/mobile/how-to-get-developer-options-on-android/

From Developer Options settings, set "Bluetooth HCI snoop log" to enabled. 

After starting and running VictronConnect for a short while, go back into Developer Options and click "Take bug report", select "Full report" and share the report with yourself somehow.

Depending on android version, you can either unzip the bug report and find the file *FS/data/log/bt/btsnoop_hci.log* or you might need to use the btsnooz script available here https://android.googlesource.com/platform/system/bt/+/master/tools/scripts/btsnooz.py

* Get btsnooz.py.
* Extract the text version of the bug report.
* Run btsnooz.py on the text version of the bug report:
* `btsnooz.py BUG_REPORT.txt > btsnoop_hci.log`

The file btsnoop_hci.log can then be read by e.g. Wireshark etc.


The most interessting thing is what UUIDs the different devices are expecting writes and sending notifies on.  And whether the init-session is the same for all devices.

Also, it seems like I need to send a write request from time to time to keep the notifications flowing.



