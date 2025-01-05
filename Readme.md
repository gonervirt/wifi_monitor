# WiFi Monitor for ESP32-S2

This project is a WiFi monitoring script for the ESP32-S2 microcontroller using MicroPython. The script measures the WiFi connection quality by monitoring three values: RSSI (signal strength), round trip time to the gateway, and round trip time to an external website (Google). The data and events are logged in three different ways: to an SD card, to ThingSpeak, and displayed on a web page.

## Features

- Measures WiFi signal strength (RSSI)
- Measures round trip time to the gateway
- Measures round trip time to an external website (Google)
- Logs data to an SD card in CSV format
- Sends data to ThingSpeak
- Displays the latest measurements on a web page
- Provides a button on the web page to stop monitoring gracefully
- Synchronizes time with an NTP server (UTC+1)

## Configuration

The configuration parameters for WiFi and ThingSpeak are stored in a JSON file named `config.json`. The file should be placed in the root directory of the SD card.

### config.json

```json
{
    "WIFI_SSID": "your_wifi_ssid",
    "WIFI_PASSWORD": "your_wifi_password",
    "THINGSPEAK_API_KEY": "your_thingspeak_api_key"
}
```

## Installation

1. Copy the `wifi_monitor.py`, `main.py`, and `config.json` files to the root directory of the SD card.
2. Insert the SD card into the ESP32-S2.
3. Connect the ESP32-S2 to your computer and upload the files using a tool like `ampy` or `rshell`.

## Usage

1. Power on the ESP32-S2.
2. The script will automatically start monitoring the WiFi connection.
3. Access the web page hosted by the ESP32-S2 to view the latest measurements and stop monitoring if needed.

## File Structure

```
/sd
├── config.json
├── main.py
├── wifi_monitor.py
└── logs
    └── *.csv
```

## Classes

### Config

Loads configuration parameters from the `config.json` file.

### Logger

Handles logging of events and data to the SD card and ThingSpeak.

### WebServer

Hosts a web server to display the latest measurements and provide a button to stop monitoring.

### WiFiMonitor

Main class that initializes the WiFi connection, starts monitoring, and handles synchronization of time.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```

This `README.md` file provides an overview of the project, configuration instructions, installation steps, usage information, file structure, and descriptions of the main classes.