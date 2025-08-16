## BOK_SURVEY
* [x] in read_from_emlid, read EMLID data from the usb Serial connection (passed with NMEA2 format an print lat, lon, altitude and precise time
* [x] I want a function that detect the name of the EMLID USB file descriptor, working both on Mac OS and raspberry PI
  * Implemented in `bok_survey.find_emlid_device()` - See [emlid_device_detection.md](emlid_device_detection.md) for usage
* [ ] In the survey.analysis.gps packaoge, I want a function that takes a GPSPoint object in referentiel from WGS84 GPS coordinates. I want to convert them as a tuple of three float in UTM zone 34 N coordinates, with x, y and z. Use pyproj package
* 