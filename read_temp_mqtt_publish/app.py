# Source: Electrocredible.com, Language: MicroPython
VERSION="0.0.2"
from machine import reset
import time
import secrets
import machine
import network
import time
import onewire, ds18x20
import gc

from umqtt.simple import MQTTClient
from ssd1306 import SSD1306_I2C
from ota import OTAUpdater
from WIFI_CONFIG import SSID, PASSWORD

import senko

global use_oled
use_oled = False

gc.enable()

global WDT
WDT = False

# setup to WiFi
global wlan
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

#### functions ###

def __init__():

  TESTING_NO_SENSOR = False

  ds_pin = machine.Pin(22, machine.Pin.PULL_UP)

  # setup to WiFi
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  wlan.connect(SSID, PASSWORD)


def connect_to_wifi(wlan):
  global use_oled
  global WDT
  WIDTH =128 
  HEIGHT= 64
  i2c=machine.I2C(0,scl=machine.Pin(9),sda=machine.Pin(8),freq=200000)
  if i2c.scan():
    use_oled = True

  if use_oled:
    oled = SSD1306_I2C(WIDTH,HEIGHT,i2c)

  # connect to wifi function
  message = "Wating for Wifi ..."
  print("{0}".format(message))
  if use_oled:
    oled.text("{0}".format(message), 0, 0)
    oled.fill(0)
    oled.show()
    
  count = 0
  while wlan.isconnected() == False:
    if WDT:
      WDT.feed()
    message="Wating for Wifi ..."
    print("{0}".format(message))
    if use_oled:
      oled.fill(0)
      time.sleep(0.2)
      oled.show()
      oled.fill(0)
      oled.text("{0}".format(message), 0, 10)
      oled.text("fail count : {0}".format(count), 0, 20)
      oled.show()
    print("fail count : {0}".format(count))
    count += 1
    if count > 30:
      machine.reset()
    time.sleep(2)
  message="Connected to WiFi"
  if use_oled:
    oled.fill(0)
    oled.text("{0}".format(message), 0, 0)
    oled.show()
  print("{0}".format(message))


def read_temp_publish():
  global use_oled
  global WDT
  mqtt_host = "192.168.0.202"
  mqtt_username = ""  # Your Adafruit IO username
  mqtt_password = ""  # Adafruit IO Key

  WIDTH =128 
  HEIGHT= 64
  i2c=machine.I2C(0,scl=machine.Pin(9),sda=machine.Pin(8),freq=200000)
  if i2c.scan():
    use_oled = True
  if use_oled:
    oled = SSD1306_I2C(WIDTH,HEIGHT,i2c)


  time.sleep(0.5)
  ds_pin = machine.Pin(22, machine.Pin.PULL_UP)


#  OTA_UPDATE_GITHUB_REPOS = {
#      "euridium/pi_pico_w_auto": ["read_temp_publish_oled_v2.py"]
#  }
#
#  ota_updater = OTAUpdater(
#    secrets.GITHUB_USER,
#    secrets.GITHUB_TOKEN,
#    OTA_UPDATE_GITHUB_REPOS,
#    # update_interval_minutes=60,  # Set the update interval to 60 minutes
#    debug=True,
#    save_backups=True
#  )
#
#  ota_updater.updated()  # Check for updates, and apply if available
#  print("MAIN: Updates checked. Continuing with the main code...")


  # Initialize our MQTTClient and connect to the MQTT server
  mqtt_client_id = "pico_boiler_temps_1"
  mqtt_client = MQTTClient(
    client_id=mqtt_client_id,
    server=mqtt_host,
    user=mqtt_username,
    password=mqtt_password)
 

  # connect to wifi
  connect_to_wifi(wlan)
  #connect to mqtt
  mqtt_client.connect()


  fail_counter = 0
  while True:
    WDT.feed()
    try:
      TESTING_NO_SENSOR = False
      # confirm and reconnect wireless
      while wlan.isconnected() == False:
        # connect to wifi
        connect_to_wifi(wlan)
        #connect to mqtt
        mqtt_client.connect()
        time.sleep(1)

      # short screen blank and delay to make the visible screen flicker (so you know it is changing)
      if use_oled:
        oled.fill(0)
        oled.show()
        time.sleep(0.1)

      ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
      roms = ds_sensor.scan()

      if not roms:
        message = "no roms"
        if use_oled:
          oled.fill(0)
          oled.text("{0}".format(message), 0, 0)
          oled.show()
        print("{0}".format(message))

        TESTING_NO_SENSOR = True
        time.sleep(1)
      
      if TESTING_NO_SENSOR:
        # do fake stuff
        fake_address = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        fake_temp = "25.1"
    

        mqtt_publish_topic = "pico-test"  # The MQTT topic for your Adafruit IO Feed
        # message = fake_address + " : " + fake_temp
        message = "{0} : {1}".format(fake_address[-6:], fake_temp)
        if use_oled:
          oled.fill(0)
          oled.text("{0}".format(message), 0, 0)
          oled.show()
        print("{0}".format(message))
 
        # Publish the data to the topic!
        mqtt_client.publish(mqtt_publish_topic + '/' + fake_address, fake_temp)
      else: 
        mqtt_publish_topic = "pi-test/boiler_temps"  # The MQTT topic for your Adafruit IO Feed

        ds_sensor.convert_temp()
        time.sleep_ms(750)
        if use_oled:
          oled.fill(0)
        message_pos = 0
        for rom in roms:
          device_address = '' . join('{:02x}'.format(x) for x in rom)
          device_temp = str(round(ds_sensor.read_temp(rom),1))
          # print("{0}  {1}  {2}".format(rom, device_address, device_temp))
          message = "{0} : {1}".format(device_address[-6:], device_temp)
          print("{0}".format(message))
          if use_oled:
            oled.text("{0}".format(message), 0, message_pos)
          message_pos += 10
     
          # Publish the data to the topic!
          mqtt_client.publish(mqtt_publish_topic + '/' + device_address, device_temp)

        if use_oled:
          oled.show()
        # Delay a bit to avoid hitting the rate limit
      time.sleep(5)

    except Exception as e:
      fail_counter += 1
      if use_oled:
        oled.fill(0)
        oled.show()
      time.sleep(0.5)
      message = "exp: ".format(e)
      if use_oled:
        oled.fill(0)
        oled.text("{0}".format("read temp"), 0, 0)
      print("{0}".format("read temp"))
      print("{0}".format(message))
      if use_oled:
        oled.text("{0}".format(message), 0, 10)
        oled.text("fail count : {0}".format(fail_counter), 0, 20)
        oled.show()
 
      if fail_counter > 10:
        #reset
        machine.reset()
      time.sleep(5)



def entry():
  
  global use_oled
  global wlan
  global WDT
  WIDTH =128 
  HEIGHT= 64
  i2c=machine.I2C(0,scl=machine.Pin(9),sda=machine.Pin(8),freq=200000)
  if i2c.scan():
    use_oled = True

  if use_oled:
    oled = SSD1306_I2C(WIDTH,HEIGHT,i2c)
  if use_oled:
    # test screen
    oled.fill(0)
    oled.text("123456789ABCDEFG", 0, 0)
    oled.text("23456789ABCDEFGH", 0, 10)
    oled.text("3456789ABCDEFGHI", 0, 20)
    oled.text("456789ABCDEFGHIJ", 0, 30)
    oled.text("56789ABCDEFGHIJK", 0, 40)
    oled.text("6789ABCDEFGHIJKL", 0, 50)
    oled.show()
  print("Show screen")


  OTA = senko.Senko(
    user="euridium", # Required
    repo="pi_pico_w_auto", # Required
    branch="main", # Optional: Defaults to "master"
    working_dir="read_temp_mqtt_publish", # Optional: Defaults to "app"
    files = ["app.py", "main.py"]
  )  

  # connect to wifi
  connect_to_wifi(wlan)

  message="checking updates"
  print("{0}".format(message))
  if use_oled:
    oled.fill(0)
    oled.text("{0}".format(message), 0, 10)
    oled.show()
  if OTA.update():
    if use_oled:
      message="updated. reboot"
      oled.fill(0)
      oled.text("{0}".format(message), 0, 10)
      oled.show()
    print("Updated to the latest version! Rebooting...")
    machine.reset()

  WDT = machine.WDT(timeout=8300)
  read_temp_publish()
  

if __name__ == "__main__":
  entry() 


