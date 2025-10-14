import network
import socket
import time
from machine import Pin

led = Pin('LED', Pin.OUT)

html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>My First Pico Server</title>
</head>
<body>
    <h1>Hello from Pico!</h1>
    <p>This is my first web server running on a Raspberry Pi Pico W.</p>
</body>
</html> 
""" 
# Connect to Wi-Fi
ssid = 'prettyFly4aWiFi'
password = 'password1234'
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
 
# Wait for connection
while not wlan.isconnected():
    print('Connecting to Wi-Fi...')
    led.value(not led.value())
    time.sleep(1)
 
print('Connected to Wi-Fi')
ip_address = wlan.ifconfig()[0]  # Get the IP address
print('IP Address:', ip_address)
 
# Create a socket to listen on port 80
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
 
print('Listening on port 80...')
# Main loop
for i in range(10):
    led.value(not led.value())
    time.sleep(0.1)

while True:
    conn, addr = s.accept()
    print(f'Got a connection from {str(addr)}')
    request = conn.recv(1024) 
    request_str = str(request)
    print('Content = %s' % request_str)
    
    # Serve the HTML page for any request
    body = html_page if isinstance(html_page, bytes) else html_page.encode('utf-8')
    
    headers = (
    'HTTP/1.1 200 OK\r\n'
    f'Content-Type: text/html; charset=utf-8\r\n'
    f'Content-Length: {len(body)}\r\n'
    'Connection: close\r\n'
    '\r\n'
    ).encode('utf-8')
    conn.send(headers)
    conn.sendall(body)
    conn.close()
    
    """
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(html_page)
    conn.close()
    """