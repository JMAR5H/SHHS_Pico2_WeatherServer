import network
import socket
import ntptime
import time
from machine import Pin
#import _thread



# HTML_Render
def read_html_file(file_path):
    """Reads an HTML file and returns its contents as a string."""
    print("Reading HTML file:", file_path)
    with open(file_path, 'r') as f:
        return f.read()


def render_html(file_path, **context):
    """
    Pico-compatible HTML renderer supporting:
    - {{ variable }}
    - {% extends "base.html" %}
    - {% block name %} ... {% endblock %}
    """
    full_path = "templates/" + file_path 
    html = read_html_file(full_path)
    print("Rendering HTML from:", full_path)

    # --- Handle extends ---
    base_template = None
    if '{% extends "' in html:
        # Extract base file name
        start = html.find('{% extends "') + len('{% extends "')
        end = html.find('" %}', start)
        base_file = html[start:end]
        base_template = read_html_file(base_file)

        # Extract all blocks from child
        blocks = {}
        pos = 0
        while True:
            start_block = html.find('{% block ', pos)
            if start_block == -1:
                break
            start_name = start_block + len('{% block ')
            end_name = html.find('%}', start_name)
            block_name = html[start_name:end_name].strip()
            end_block = html.find('{% endblock %}', end_name)
            block_content = html[end_name + 2:end_block].strip()
            blocks[block_name] = block_content
            pos = end_block + len('{% endblock %}')

        # Replace blocks in base template
        print("Merging with base template:", base_file)
        rendered = base_template
        for name, content in blocks.items():
            tag_start = '{% block ' + name + ' %}'
            tag_end = '{% endblock %}'
            s = rendered.find(tag_start)
            e = rendered.find(tag_end, s)
            if s != -1 and e != -1:
                rendered = rendered[:s] + content + rendered[e + len(tag_end):]
    else:
        rendered = html

    # --- Replace {{ variables }} ---
    print("Replacing context variables:", context)
    for key, value in context.items():
        rendered = rendered.replace('{{ ' + key + ' }}', str(value))
        rendered = rendered.replace('{{' + key + '}}', str(value))

    # --- Return as bytes ---
    print("Final rendered HTML length:", len(rendered))
    if isinstance(rendered, bytes):
        return rendered
    else:
        return rendered.encode('utf-8')


class Request:
    def __init__(self, byteRequest):
        self.method = byteRequest.get('method', 'GET')
        self.path = byteRequest.get('path', '/')
        self.form = byteRequest.get('form', {})

    def __repr__(self):
        return f"<Request method={self.method} path={self.path} form={self.form}>"
    def __str__(self):
        return self.__repr__()
    
class PicoLiteServer:
    def __init__(self, ssid, password, threadHardwareMonitor=False):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)
        self._routes = {}
        self._devices = {}
        self.interval = 2  # seconds between device checks
        self.led = Pin('LED', Pin.OUT)
        self.runthread = threadHardwareMonitor  #whether to run device monitor thread


    def connect_wifi(self):
        """
        networks = self.wlan.scan()
        print('Available networks:')
        for net in networks:
            print(f' - {net[0].decode("utf-8")} (RSSI: {net[3]}) Security: {net[4]} Channel: {net[2]} Hidden: {net[5]} BSSID: {net[1].hex()}        ')  
        """
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
     
        # Wait for connection
        print('Connecting to Wi-Fi...')
        while not self.wlan.isconnected():
            self.led.value(not self.led.value())
            time.sleep(1)
        
        for i in range(10):
            self.led.value(not self.led.value())
            time.sleep(0.1)
        
        print('Connected to Wi-Fi')
        ip_address = self.wlan.ifconfig()[0]  # Get the IP address
        print('IP Address:', ip_address)

    def route(self, path):  #to do methods
        """
        Decorator to register a route handler for a given path.
        Usage:
            @server.route("/")
            def index(request):
                return "<h1>Hello</h1>"
        """
        if not hasattr(self, '_routes'):
            self._routes = {}
        def decorator(func):
            self._routes[path] = func
            return func
        return decorator
    
    def device(self, device_object):
        """
        decorator to register a device (e.g., sensor or display).   """
        if not hasattr(self, '_devices'):
            self._devices = {}
        #self._devices[device_object.id] = device_object
        #return device_object
        def decorator(func):
            self._devices[device_object] = func
            return func
        return decorator

    def device_monitor(self):
        """Function to monitor and interact with registered devices."""
        time.sleep(self.interval)
        if not hasattr(self, '_devices'):
            return # No devices to monitor
        while True:
            time.sleep(self.interval)  # Adjust the interval as needed
            for device, func in self._devices.items():
                time.sleep(self.interval)
                try:
                    func(device)
                except Exception as e:
                    print("Error handling device:", e)

    def set_time(self):
        try:
            ntptime.host = 'pool.ntp.org' # Or a regional NTP server
            ntptime.settime()
            print("Time synchronized successfully.")
        except OSError as e:
            if e.args[0] == 110: # ETIMEDOUT
                print("Error: NTP server timed out. Check network or server availability.")
            else:
                print(f"An unexpected error occurred: {e}")        

    def start_server(self):
        # Create a socket to listen on port 80
        self.connect_wifi()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 80))
        s.listen(5) # Listen for incoming connections

        

        print('Listening on port 80...')
        # Main loop
        if hasattr(self, '_devices') and self._devices and self.runthread:
            import _thread
            _thread.start_new_thread(self.device_monitor, ())

        # start device monitoring on 2nd core thread.
        #_thread.start_new_thread(self.device_monitor, ())
        time.sleep(2) #give time for wifi to stabilise 
        self.set_time()

        while True:
            time.sleep(self.interval)  # Adjust the interval as needed
            
            #NEW code attempting to avoid threading issues
            for device, func in self._devices.items():
                try:
                    func(device)
                except Exception as e:
                    print("Error handling device:", e)
            
            try:
                conn, addr = s.accept()                 
                
                print(f'Got a connection from {str(addr)}')
                request = conn.recv(1024)

                print("Received request method:", request.method)
                print("Received request form:", request.form.get('example_field', 'N/A'))
                request_str = request.decode('utf-8')
                #print('Content = %s' % request_str)
                
                # Parse HTTP request
                try:
                    request_line = request_str.split('\r\n')[0]
                    #print("Request line:", request_line)
                    method, path, _ = request_line.split()
                    path = path.split('?')[0]  # Ignore query parameters
                    print(f"Request for path: {path}")
                    handler = self._routes.get(path, None) 
                    if handler:
                        response_body = handler(request)  # Call the handler
                        if isinstance(response_body, str):
                            response_body = response_body.encode('utf-8')
                    else:
                        response_body = b"404 Not Found"
                except Exception as e:
                    response_body = b"400 Bad Request"
                    print("Error parsing request:", e)
                headers = {
                    'Content-Type': 'text/html',
                    'Content-Length': str(len(response_body)),
                    'Connection': 'close'
                }
                response_headers = "\r\n".join(f"{key}: {value}" for key, value in headers.items())
                conn.sendall(f"HTTP/1.1 200 OK\r\n{response_headers}\r\n\r\n".encode('utf-8'))
                conn.sendall(response_body)
                conn.close()    
            except Exception as e:
                    print("error: ",e)



