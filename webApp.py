import picoLiteServer as pls
import ssd1306
import machine
import bme280
import framebuf
from time import sleep, localtime
print("Lets gooooo!")
ssid = "Your_SSID_here"
password = "Your_PASSWORD_here"
server = pls.PicoLiteServer(ssid=ssid, password=password)
server.interval = 1 #seconds between device checks
#server.runthread = True
print("PicoLiteServer initialized")

# Raspberry Pi logo as 32x32 bytearray
buffer = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c \x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

# Load the raspberry pi logo into the framebuffer (the image is 32x32)
fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB)
# Initialize BME280 sensor 
i2c = machine.I2C(0,sda= machine.Pin(0), scl=machine.Pin(1), freq=400000)
bme = bme280.BME280(i2c=i2c)

# Initialize OLED display
i2c_display = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3), freq=400000)
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c_display)

leds = [machine.Pin(17, machine.Pin.OUT), machine.Pin(14, machine.Pin.OUT), machine.Pin(9, machine.Pin.OUT)]
ledcount = 0
temp, pres, hum = bme.values
time = localtime()
display_message = ""
display_items = ['time', 'temp', 'pres', 'ip']

@server.device(bme)
def read_bme280(sensor):
    global temp, pres, hum, ledcount # Use global to modify the outer scope variables
    try:
        temp, pres, hum = sensor.values
        print(f"BME280 Readings - Temperature: {temp}, Pressure: {pres}, Humidity: {hum}")
    except Exception as e:
        print("Error reading BME280 sensor:", e)

    ledcount = (ledcount + 1) % len(leds)
    leds[ledcount].value(not leds[ledcount].value())

@server.device(oled)
def update_oled(display):
    x = 0
    y = 0
    display.fill(0)  # Clear the display
    global display_message
    if 'time' in display_items:
        time = localtime()
        display.text(f"Time: {time[3]:02}:{time[4]:02}", x, y)
        y += 10
    if 'temp' in display_items:
        display.text(f"Temp: {temp}", x, y)
        y += 10
    if 'pres' in display_items:
        display.text(f"Baro: {pres}", x, y)
        y += 10
    if 'ip' in display_items:
        ipaddr = server.wlan.ifconfig()[0]
        display.text(f"IP: {ipaddr}", x, y) 
        y += 10
    if 'display_message' in display_items:
        display.text(display_message, x, y)
        y += 10
    display.show()
    """ Simple direct approach
    ipaddr = server.wlan.ifconfig()[0]
    time = localtime()
    print("time:", time)
    try:
        #temp, pres, hum = bme.values
        display.fill(0)  # Clear the display
        # draw scaled time text (scale factor)
        display.text(f"{time[3]:02}:{time[4]:02}", 60, 0)
        display.text("Room temp & Baro", 0, 20)
        display.text(f"T: {temp}", 0, 30)
        display.text(f"P: {pres}", 0, 40)
        display.text(str(ipaddr), 0, 50)
        display.text(str(ledcount), 110, 40)
        #oled.blit(fb, 96, 35)
        display.show()
        print("OLED display updated")
    except Exception as e:
        print("Error updating OLED display:", e)
        """


@server.route("/")
def index(request):
    return pls.render_html("index.html", title="My First Pico Server", name="John", site_name="Pico Web")  


@server.route("/about")
def about(request):
    print("\n\nHandling request for /about\n\n")
    return pls.render_html("firsthtml.html") 

@server.route("/lc")
def led_control(request):
    print("\n\nHandling request for /ledcontrol\n\n")
    return pls.render_html("ledcontrol.html")

@server.route("/Light_control")
def light_control(request):
    print("\n\nHandling request for /Light_control\n\n")
    if request.method == "POST":
        request.form
        print("Parsed parameters:", request.form)
        if "red" in request.form:
            print("Red light requested")
            leds[0].value(not leds[0].value())
        if "blue" in request.form:
            print("Blue light requested")
            leds[1].value(not leds[1].value())
        if "white" in request.form:
            print("White light requested")
            leds[2].value(not leds[2].value())
        return pls.render_html("light_control.html", red_led=leds[0].value(), blue_led=leds[1].value(), white_led=leds[2].value())
    else:
        return pls.render_html("light_control.html", red_led=leds[0].value(), blue_led=leds[1].value(), white_led=leds[2].value())
    

@server.route("/update_display")
def update_display(request): # METHOD=["GET", "POST"]
    print("\n\nHandling request for /update_display\n\n")
    global display_message # we will modify this variable so we need to declare it global    

    if request.method == "GET" and request.path == "/update_display":
        print("Processing GET /update_display")
        return pls.render_html("updateDisplay.html", current_message=display_message, weather_display='temp' in display_items, time_display='time' in display_items, ip_display='ip' in display_items)
    
        # GET IS FUNCTIONAL... FIX POST
    elif request.method == "POST" and request.path == "/update_display":
        print("Processing POST /update_display")
        try:
            params = request.form
            print("Parsed parameters:", params)
            display_items.clear()
            if "time" in params:
                display_items.append('time')
            if "message" in params:
                display_items.append('display_message')
                message = params["message"].replace("+", " ")
                display_message = message
                print(f"display_message set to: {display_message}")
                print("Added message to display:", message)
            if "weather" in params:
                display_items.append("temp")
                display_items.append("pres")
            if "ip" in params:
                display_items.append("ip")
        except Exception as e:
            print("Error processing update_display request:", e)
    return pls.render_html("updateDisplay.html", current_message=display_message, weather_display='temp' in display_items, time_display='time' in display_items, ip_display='ip' in display_items)

@server.route("/ledtoggle")
def led_toggle(request):

    print("\n\nHandling request for /led_toggle\n\n")
    server.led.value(not server.led.value())
    ledState = "ON" if server.led.value() else "OFF"
    for c in range(10):
        for led in leds:
            sleep(0.2)
            led.value(not led.value())   
    return ledState.encode('utf-8')

@server.route("/LED_Flash")
def led_flash(request):
    print("\n\nHandling request for /LED_Flash\n\n")
    for c in range(5):
        for led in leds:
            led.value(1)
        sleep(0.5)
        for led in leds:
            led.value(0)
        sleep(0.5)
    return "LEDs flashed!".encode('utf-8')

@server.route("/save")
def save_data(request):
    print(f"\n\nHandling request for /save, Method: {request.method}\n\n")
    if request.method == "GET" and request.path.startswith("/save?"):
        try:
            params = request.args
            print("Parsed parameters:", params)
            text = params.get("text", "")
            print("Text to save:", text)
            with open("templates/data.txt", "a") as f:
                f.write(text)
            print("Data saved to file")
            return "Data saved successfully!"
        except Exception as e:
            print("Error processing save request:", e)
            return "Error saving data."
def Old_save_data(request):
    # open templates/data.txt
    request_str = request.decode('utf-8') #From before using request object

    print("Request string:", request_str)
    if "GET /save?" in request_str:
        try:
            query = request_str.split("GET /save?")[1].split(" ")[0]
            print("Query string:", query)
            params = {}
            for pair in query.split("&"):
                key, value = pair.split("=")
                params[key] = value
            print("Parsed parameters:", params)
            text = params.get("text", "")
            print("Text to save:", text)
            with open("templates/data.txt", "w") as f:
                f.write(text)
            print("Data saved to file")
            return "Data saved successfully!"
        except Exception as e:
            print("Error processing save request:", e)
            return "Error saving data."

@server.route("/save_text")
def save_text(request):                                             
    print("\n\nHandling request for /save_text\n\n")
    if request.method == "GET":
        print("Get Method detected")
        return pls.render_html("sendTextToFile.html")
    if request.method == "POST":
        print("Post Method detected")
        try:
            params = request.form
            print("Parsed parameters:", params)
            text = params.get("text", "")
            print("Text to save:", text)
            with open("templates/data.txt", "a") as f: 
                f.write(text+', ')
            print("Data saved to file")
            return pls.render_html("sendTextToFile.html", message="Data saved successfully!")
        except Exception as e:
            print("Error processing save_text request:", e)
            return pls.render_html("sendTextToFile.html", message="Error saving data.")
    else:
        print("Non-POST method detected")
        return pls.render_html("sendTextToFile.html", message="")

@server.route("/login")
def login(request):
    print("\n\nHandling request for /login\n\n")
    if request.method == "POST":
        try:
            params = request.form
            print("Parsed parameters:", params)
            username = params.get("username", "")
            password = params.get("password", "")
            print(f"Username: {username}, Password: {password}")
            if username == "admin" and password == "password":
                return "Login successful!"
            else:
                return "Invalid credentials."
        except Exception as e:
            print("Error processing login request:", e)
            return "Error during login."
    else:   
        return pls.render_html("login.html")    

@server.route("/viewdata")
def view_data(request):
    print("\n\nHandling request for /viewdata\n\n")
    try:
        with open("templates/data.txt", "r") as f:
            data = f.read()
        return data
    except Exception as e:
        print("Error reading data file:", e)
        return "Error reading data."
    

#print("Registered routes:", server._routes)
oled.text("Looking for WiFi", 0, 0)
oled.blit(fb, 50, 15)
oled.show()

server.start_server()

