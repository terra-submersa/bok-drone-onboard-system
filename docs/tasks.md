## BOK_SURVEY
* [x] in read_from_emlid, read EMLID data from the usb Serial connection (passed with NMEA2 format an print lat, lon, altitude and precise time
* [x] I want a function that detect the name of the EMLID USB file descriptor, working both on Mac OS and raspberry PI
  * Implemented in `bok_survey.find_emlid_device()` - See [emlid_device_detection.md](emlid_device_detection.md) for usage