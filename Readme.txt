as a senior developper, Could you create a micropython script, for esp32s2, that would monitor the wifi connection quality. For that script make sure to take into account all requirements below, make proper design, and add usefull comments in code.  The script will measure 3 values, and the scrip should be resilient to wifi Failure (and log errors accordingly in log files) :
the power (rssi), 
the round trip to the Gateway, 
and the round trip to internet (google web site). 

The data and events should be logged in 3 différents ways:
- in csv file (separated by ;), stored on sd card, column should be  wifi ssid, time stamp, event type, rssi, round trip to Gateway, and round trip to google.  Writing to the sd card should be limited, to one time by hours in different file . 
- the data ( rssi, round trip to Gateway, and round trip to google) should also be sent to thinkspeak
- and latests logs should be displayed on a webpage, the top of the web page should propose a button to stop the monitoring and finish gracefully (writing log file, sending data to thinkspeak)


time stamp should be sync with ntp, time zone utc+1.
instead of several file, coud you put all of them in one file, in different class


could you add a log_event function in Logger class, that will then dispatch log in sdcard, thingspeak, webpage, and make sur ethe function is colled corrcetly all over the code