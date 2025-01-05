import network
import urequests
import time
import machine
import os
import sdcard
import ntptime
import json
import socket
from machine import Pin, SPI, RTC

class Config:
    # Load configuration from JSON file
    with open('config.json') as config_file:
        config = json.load(config_file)
    
    # WiFi Configuration
    WIFI_SSID = config.get("WIFI_SSID", "default_ssid")
    WIFI_PASSWORD = config.get("WIFI_PASSWORD", "default_password")
    
    # ThingSpeak Configuration
    THINGSPEAK_API_KEY = config.get("THINGSPEAK_API_KEY", "default_api_key")
    THINGSPEAK_URL = "https://api.thingspeak.com/update"
    
    # Monitoring Configuration
    MEASUREMENT_INTERVAL = 60  # seconds
    LOG_INTERVAL = 3600       # 1 hour in seconds
    GOOGLE_HOST = "www.google.com"
    NTP_SERVER = "pool.ntp.org"
    TIMEZONE_OFFSET = 3600    # UTC+1
    
    # SD Card Configuration
    SD_MOUNT_POINT = "/sd"
    LOG_FOLDER = "/sd/logs"
    
    # Web Server Configuration
    WEB_PORT = 80

class Logger:
    def __init__(self):
        self._ensure_log_directory()
        self.latest_measurements = []
    
    def _ensure_log_directory(self):
        try:
            os.mkdir('/sd/logs')
            print("Created /sd/logs")
        except:
            print("Directory /sd/logs already exists")
    
    def _format_timestamp(self, timestamp):
        tm = time.localtime(timestamp)
        return f"{tm[0]:04d}-{tm[1]:02d}-{tm[2]:02d} {tm[3]:02d}:{tm[4]:02d}:{tm[5]:02d}"
    
    def log_to_file(self, metrics):
        try:
            year, month, day = time.localtime()[:3]
            filename = f"{Config.LOG_FOLDER}/{year}_{month}_{day}.csv"
            line = f"{metrics['ssid']};{self._format_timestamp(metrics['timestamp'])};{metrics['event_type']};{metrics['rssi']};{metrics['gateway_rtt']};{metrics['google_rtt']}\n"
            
            with open(filename, 'a') as f:
                f.write(line)
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def send_to_thingspeak(self, metrics):
        try:
            params = {
                'api_key': Config.THINGSPEAK_API_KEY,
                'field1': metrics['rssi'],
                'field2': metrics['gateway_rtt'],
                'field3': metrics['google_rtt']
            }
            url = f"{Config.THINGSPEAK_URL}?api_key={params['api_key']}&field1={params['field1']}&field2={params['field2']}&field3={params['field3']}"
            response = urequests.get(url)
            if response.status_code != 200:
                print(f"ThingSpeak error: {response.status_code} - {response.text}")
            response.close()
        except Exception as e:
            print(f"ThingSpeak error: {e}")
    
    def log_event(self, event_type, rssi=None, latency_gw=None, latency_internet=None, notes=""):
        metrics = {
            'ssid': Config.WIFI_SSID,
            'timestamp': time.time() + Config.TIMEZONE_OFFSET,
            'event_type': event_type,
            'rssi': rssi,
            'gateway_rtt': latency_gw,
            'google_rtt': latency_internet,
            'notes': notes
        }
        
        # Print event to console
        print(f"Event: {event_type}, Time: {self._format_timestamp(metrics['timestamp'])}, RSSI: {rssi}, Gateway RTT: {latency_gw}, Google RTT: {latency_internet}, Notes: {notes}")
        
        # Log to SD card
        self.log_to_file(metrics)
        
        # Send to ThingSpeak
        self.send_to_thingspeak(metrics)
        
        # Update latest measurements
        if event_type == "measurement":
            self.latest_measurements.append(metrics)
            if len(self.latest_measurements) > 5:
                self.latest_measurements.pop(0)

class WebServer:
    def __init__(self, wifi_monitor):
        self.wifi_monitor = wifi_monitor
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', Config.WEB_PORT))
        self.socket.listen(1)
    
    def handle_request(self, conn):
        try:
            request = conn.recv(1024).decode()
            
            if 'GET /stop' in request:
                self.wifi_monitor.stop()
                response = self._create_json_response({'status': 'stopping'})
            elif 'GET /metrics' in request:
                response = self._create_json_response(self.wifi_monitor.logger.latest_measurements)
            else:
                response = self._create_html_response()
            
            conn.send(response)
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            conn.close()
    
    def _create_html_response(self):
        html = '''HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
        <!DOCTYPE html>
        <html>
            <head>
                <title>WiFi Monitor</title>
                <meta http-equiv="refresh" content="30">
                <style>
                    body { font-family: Arial; margin: 20px; }
                    .metrics { margin-top: 20px; }
                    button { padding: 10px; background: #ff4444; color: white; border: none; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <button onclick="fetch('/stop')">Stop Monitoring</button>
                <div class="metrics">
                    <h2>Latest Measurements</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>RSSI</th>
                                <th>Gateway RTT</th>
                                <th>Google RTT</th>
                            </tr>
                        </thead>
                        <tbody id="metricsData"></tbody>
                    </table>
                </div>
                <script>
                    fetch('/metrics')
                        .then(response => response.json())
                        .then(data => {
                            const tableBody = document.getElementById('metricsData');
                            tableBody.innerHTML = '';
                            data.forEach(metric => {
                                const row = document.createElement('tr');
                                row.innerHTML = `
                                    <td>${metric.timestamp_formatted}</td>
                                    <td>${metric.rssi}</td>
                                    <td>${metric.gateway_rtt}</td>
                                    <td>${metric.google_rtt}</td>
                                `;
                                tableBody.appendChild(row);
                            });
                        });
                </script>
            </body>
        </html>'''
        return html.encode()
    
    def _create_json_response(self, data):
        formatted_data = []
        for metric in data:
            if isinstance(metric, dict):
                metric_copy = metric.copy()
                metric_copy['timestamp_formatted'] = self.wifi_monitor.logger._format_timestamp(metric['timestamp'])
                formatted_data.append(metric_copy)
        return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{json.dumps(formatted_data)}".encode()
    
    def close(self):
        self.socket.close()

class WiFiMonitor:
    def __init__(self):
        print("Initializing WiFi Monitor...")
        self.running = True
        self.latest_measurements = {}
        self._init_sd_card()
        self.logger = Logger()
        self._init_wifi()
        
    
    def start(self):
        print("Starting WiFi Monitor...")
        try:
            self.web_server = WebServer(self)
            #self._sync_time()
            self._start_monitoring()
        except Exception as e:
            print(f"Fatal error: {e}")
            self.stop()
    
    def _init_wifi(self):     
        """Attempt to connect to WiFi"""
        # Initialize WiFi
        print("Initializing WiFi...")
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if self.wlan.isconnected():
            self.wlan.disconnect()
        try:
            if not self.wlan.isconnected():
                print(f"Connecting to WiFi network: {Config.WIFI_SSID}")
                self.wlan.connect(Config.WIFI_SSID, Config.WIFI_PASSWORD)
                
                # Wait up to 10 seconds for connection
                start_time = time.time()
                while not self.wlan.isconnected() and time.time() - start_time < 10:
                    time.sleep(1)
                
                if self.wlan.isconnected():
                    self.ip_address = self.wlan.ifconfig()[0]
                    print(f"WiFi connected successfully. IP: {self.ip_address}")
                    self.consecutive_failures = 0
                    self.logger.log_event("connection", notes=f"WiFi connected successfully. IP: {self.ip_address}")
                    self._sync_time()  # Sync time after successful connection
                    return True
                else:
                    self.ip_address = None
                    print("WiFi connection failed")
                    self.logger.log_event("error", notes="WiFi connection failed")
                    return False
            return True
        except Exception as e:
            self.ip_address = None
            error_msg = f"WiFi connection error: {str(e)}"
            print(error_msg)
            self.logger.log_event("error", notes=error_msg)
            return False
        
    
    def _init_sd_card(self):
        """Initialize SD card and create necessary directories"""
        print("Initializing SD card...")
        spi = SPI(1, baudrate=40000000, polarity=0, phase=0, 
                  sck=Pin(14), mosi=Pin(15), miso=Pin(2))
        cs = Pin(13, Pin.OUT)
        self.sd = sdcard.SDCard(spi, cs)
        try:
            os.mount(self.sd, Config.SD_MOUNT_POINT)
        except Exception as e:
            print(f"Warning: Failed to mount SD card: {e}")
    
    def _sync_time(self):
        try:
            ntptime.settime()
            current_time = time.time() + Config.TIMEZONE_OFFSET
            print(f"Time synchronized: {self.logger._format_timestamp(current_time)}")
        except Exception as e:
            print(f"Warning: Time sync failed: {e}")
    
    def _measure_metrics(self):
        try:
            # Measure RSSI
            rssi = self.wlan.status('rssi')
            
            # Measure Gateway RTT (simplified)
            gateway_start = time.ticks_ms()
            gateway_rtt = -1
            if self.wlan.isconnected():
                gateway_ip = self.wlan.ifconfig()[2]  # Gateway IP
                gateway_rtt = time.ticks_diff(time.ticks_ms(), gateway_start)
            
            # Measure Google RTT using socket
            google_rtt = -1
            try:
                addr = socket.getaddrinfo(Config.GOOGLE_HOST, 80)[0][-1]
                s = socket.socket()
                s.settimeout(5)
                start = time.ticks_ms()
                s.connect(addr)
                google_rtt = time.ticks_diff(time.ticks_ms(), start)
                s.close()
            except Exception as e:
                print(f"Error measuring Google RTT: {e}")
            
            metrics = {
                'ssid': Config.WIFI_SSID,
                'timestamp': time.time(),
                'rssi': rssi,
                'gateway_rtt': gateway_rtt,
                'google_rtt': google_rtt
            }
            self.latest_measurements = metrics
            return metrics
        except Exception as e:
            print(f"Error measuring metrics: {e}")
            return None
    
    def _start_monitoring(self):
        print("Starting monitoring...")
        self._sync_time()  # Ensure time is synchronized before starting monitoring
        last_log_time = 0
        
        # Start web server in a separate thread
        import _thread
        _thread.start_new_thread(self._run_web_server, ())
        
        # Main monitoring loop
        while self.running:
            try:
                metrics = self._measure_metrics()
                if metrics:
                    # Log event
                    self.logger.log_event(
                        event_type="measurement",
                        rssi=metrics['rssi'],
                        latency_gw=metrics['gateway_rtt'],
                        latency_internet=metrics['google_rtt']
                    )
                    
                    # Log to file every hour
                    current_time = time.time()
                    if current_time - last_log_time >= Config.LOG_INTERVAL:
                        self.logger.log_event(
                            event_type="hourly_log",
                            rssi=metrics['rssi'],
                            latency_gw=metrics['gateway_rtt'],
                            latency_internet=metrics['google_rtt']
                        )
                        last_log_time = current_time
                
                time.sleep(Config.MEASUREMENT_INTERVAL)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                self.logger.log_event(event_type="error", notes=str(e))
    
    def _run_web_server(self):
        print(f"Starting web server on port {Config.WEB_PORT}") 
        while self.running:
            try:
                conn, addr = self.web_server.socket.accept()
                self.web_server.handle_request(conn)
            except Exception as e:
                print(f"Web server error: {e}")
    
    def stop(self):
        print("Stopping monitoring...")
        self.running = False
        if self.latest_measurements:
            self.logger.log_event(
                event_type="shutdown",
                rssi=self.latest_measurements['rssi'],
                latency_gw=self.latest_measurements['gateway_rtt'],
                latency_internet=self.latest_measurements['google_rtt']
            )
        self.web_server.close()

if __name__ == '__main__':
    monitor = WiFiMonitor()
    monitor.start()
