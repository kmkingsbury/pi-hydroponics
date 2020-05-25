import glob
import time
import os, sys
import logging
import yaml
import datetime

# DS18B20.py
# 2016-04-25
# Public Domain

# Typical reading
# 73 01 4b 46 7f ff 0d 10 41 : crc=41 YES
# 73 01 4b 46 7f ff 0d 10 41 t=23187
def c_to_f(temp_c = 0):
    temp_f = temp_c * 9.0 / 5.0 + 32.0
    return temp_f



with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)


# Setup MQTT
client = ''
if cfg['mqtt']['enabled'] == True:
   import paho.mqtt.client as mqtt
   client = mqtt.Client("P1") #create new instance
   client.connect(cfg['mqtt']['host']) #connect to broker
   # Loop start: These functions implement a threaded interface to the network loop. Calling loop_start() once, before or after connect*(), runs a thread in the background to call loop() automatically. This frees up the main thread for other work that may be blocking.
   client.loop_start()

while True:

   for sensor in glob.glob("/sys/bus/w1/devices/28-*/w1_slave"):
      id = sensor.split("/")[5]

      try:
         f = open(sensor, "r")
         data = f.read()
         f.close()
         if "YES" in data:
            (discard, sep, reading) = data.partition(' t=')
            t = c_to_f(float(reading) / 1000.0)
            print("{} {:.1f}".format(id, t))
            s = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
            timestamp =  s[:-3]

            if cfg['mqtt']['enabled'] == True:
                client.publish(cfg['mqtt']['topic'],  '{ "temperature_' + str(id) + '":"' + str(t) + '", "datetime":"' + str(timestamp) + '" }') # publish to mqtt
         else:
            print("999.9")

      except:
         pass

   time.sleep(1.0)
