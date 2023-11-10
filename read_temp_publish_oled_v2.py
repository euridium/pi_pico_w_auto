# Source: Electrocredible.com, Language: MicroPython
import machine
import network
import time
import onewire, ds18x20

from umqtt.simple import MQTTClient
from ssd1306 import SSD1306_I2C
from ota import OTAUpdater
from WIFI_CONFIG import SSID, PASSWORD

def read_temp_publish():
  TESTING_NO_SENSOR = True

  WIDTH =128 
  HEIGHT= 64
  # i2c=machine.I2C(1,scl=machine.Pin(27),sda=machine.Pin(26),freq=200000)
  i2c=machine.I2C(0,scl=machine.Pin(9),sda=machine.Pin(8),freq=200000)
  # i2c=I2C(0,scl=Pin(21),sda=Pin(20),freq=200000)
  #oled = SSD1306_I2C(WIDTH,HEIGHT,i2c)

  firmware_url = "https://raw.githubusercontent.com/<username>/<repo_name>/<branch_name>"








  mqtt_host = "192.168.0.202"
  mqtt_username = ""  # Your Adafruit IO username
  mqtt_password = ""  # Adafruit IO Key
  mqtt_publish_topic = "pi-test/boiler_temps"  # The MQTT topic for your Adafruit IO Feed
  mqtt_publish_topic = "pico-test"  # The MQTT topic for your Adafruit IO Feed

  print(i2c.scan())

  #i2c=I2C(0,scl=Pin(1),sda=Pin(0),freq=200000)
  oled = SSD1306_I2C(WIDTH,HEIGHT,i2c)

  # test screen
  oled.fill(0)
  oled.text("123456789ABCDEFG", 0, 0)
  oled.text("23456789ABCDEFGH", 0, 10)
  oled.text("3456789ABCDEFGHI", 0, 20)
  oled.text("456789ABCDEFGHIJ", 0, 30)
  oled.text("56789ABCDEFGHIJK", 0, 40)
  oled.text("6789ABCDEFGHIJKL", 0, 50)
  print("Show screen")
  oled.show()
  time.sleep(0.5)
    

  ds_pin = machine.Pin(22, machine.Pin.PULL_UP)

  # setup to WiFi
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  wlan.connect(SSID, PASSWORD)

  # Initialize our MQTTClient and connect to the MQTT server
  mqtt_client_id = "pico_boiler_temps_1"
  mqtt_client = MQTTClient(
    client_id=mqtt_client_id,
    server=mqtt_host,
    user=mqtt_username,
    password=mqtt_password)
 

  #### functions ###
  def connect_to_wifi(wlan):
    # connect to wifi function
    message = "Wating for Wifi ..."
    print("{0}".format(message))
    oled.text("{0}".format(message), 0, 0)
    oled.fill(0)
    oled.show()

    while wlan.isconnected() == False:
      message="Wating for Wifi ..."
      print("{0}".format(message))
      oled.fill(0)
      oled.text("{0}".format(message), 0, 10)
      time.sleep(0.2)
      oled.show()
      oled.fill(0)
      oled.text("{0}".format(message), 0, 10)
      oled.show()
      time.sleep(1)
    message="Connected to WiFi"
    oled.fill(0)
    print("{0}".format(message))
    oled.text("{0}".format(message), 0, 0)
    oled.show()

  # connect to wifi
  connect_to_wifi(wlan)
  #connect to mqtt
  mqtt_client.connect()

  fail_counter = 0
  while True:
    try:
      # confirm and reconnect wireless
      while wlan.isconnected() == False:
        # connect to wifi
        connect_to_wifi(wlan)
        #connect to mqtt
        mqtt_client.connect()
        time.sleep(1)

      # short screen blank and delay to make the visible screen flicker (so you know it is changing)
      oled.fill(0)
      oled.show()
      time.sleep(0.1)
      
      if TESTING_NO_SENSOR:
        # do fake stuff
        fake_address = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        fake_temp = "25.1"
    

        # message = fake_address + " : " + fake_temp
        message = "{0} : {1}".format(fake_address[-6:], fake_temp)
        oled.fill(0)
        print("{0}".format(message))
        oled.text("{0}".format(message), 0, 0)
        oled.show()
 
        # Publish the data to the topic!
        mqtt_client.publish(mqtt_publish_topic + '/' + fake_address, fake_temp)
      else: 
        ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
        roms = ds_sensor.scan()

        ds_sensor.convert_temp()
        time.sleep_ms(750)
        oled.fill(0)
        message_pos = 0
        for rom in roms:
          device_address = '' . join('{:02x}'.format(x) for x in rom)
          device_temp = str(round(ds_sensor.read_temp(rom),1))
          # print("{0}  {1}  {2}".format(rom, device_address, device_temp))
          message = "{0} : {1}".format(device_address[-6:], device_temp)
          print("{0}".format(message))
          oled.text("{0}".format(message), 0, message_pos)
          message_pos += 10
     
          # Publish the data to the topic!
          mqtt_client.publish(mqtt_publish_topic + '/' + device_address, device_temp)

        oled.show()
        # Delay a bit to avoid hitting the rate limit
      time.sleep(5)

    except Exception as e:
      fail_counter += 1
      oled.fill(0)
      oled.show()
      time.sleep(0.5)
      message = "exp: {e}"
      oled.fill(0)
      print("{0}".format(message))
      oled.text("{0}".format(message), 0, 0)
      oled.text("fail count : {0}".format(fail_counter), 0, 10)
      oled.show()
 
      if fail_counter > 10:
        #reset
        machine.reset()
      time.sleep(5)

if __name__ == "__main__":
  read_temp_publish()
  


