# EMLID Device Detection

This document describes how to use the EMLID device detection functionality in the BOK Drone Onboard System.

## Overview

The `find_emlid_device()` function in the `bok_survey` module automatically detects EMLID USB devices on both macOS and Raspberry Pi systems. It returns the path to the device (e.g., `/dev/tty.usbmodem1103` on macOS or `/dev/ttyACM0` on Raspberry Pi).

## Testing on macOS

To test on macOS, run:

```python
from bok_drone_onboard_system.survey import find_emlid_device

print(f'EMLID device found at: {find_emlid_device()}')
```

## Testing on Raspberry Pi

To test on Raspberry Pi, follow these steps:

1. Connect the EMLID device to the Raspberry Pi via USB
2. Run the following command:

```python
from bok_drone_onboard_system.survey import find_emlid_device

print(f'EMLID device found at: {find_emlid_device()}')
```

The function should detect the device at a path like `/dev/ttyACM0` or `/dev/ttyUSB0`.

## Troubleshooting

If the device is not detected:

1. Make sure the EMLID device is properly connected
2. Check if the device appears in the system:
   - On macOS: `ls -la /dev/tty* | grep -i usb`
   - On Raspberry Pi: `ls -la /dev/ttyACM* /dev/ttyUSB*`
3. Ensure you have the necessary permissions to access the device:
   - On Raspberry Pi, you might need to add your user to the `dialout` group:
     ```
     sudo usermod -a -G dialout $USER
     ```
     Then log out and log back in for the changes to take effect.

## Usage in Code

```python
from bok_drone_onboard_system.survey import find_emlid_device
from serial import Serial

# Find the EMLID device
emlid_device = find_emlid_device()

if emlid_device:
    print(f"EMLID device found at: {emlid_device}")
    # Connect to the device
    ser = Serial(emlid_device, 115200, timeout=1)
    # Use the connection...
else:
    print("No EMLID device found. Please check the connection.")
```