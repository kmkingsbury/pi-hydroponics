import glob
import time
import os, sys
import logging
import yaml
import datetime

import time
import board
import adafruit_dht
 
# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT11(board.D17)
 
# Typical reading
# 73 01 4b 46 7f ff 0d 10 41 : crc=41 YES
# 73 01 4b 46 7f ff 0d 10 41 t=23187
def c_to_f(temp_c = 0):
    temp_f = temp_c * 9.0 / 5.0 + 32.0
    return temp_f

def writePidFile():
    pid = str(os.getpid())
    currentFile = open('/tmp/climate_sensors.pid', 'w')
    currentFile.write(pid)
    currentFile.close()


#logging.basicConfig(level=logging.INFO, format=' %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sprinker')
logger.setLevel(logging.INFO)

fh = logging.FileHandler('./climate_sensors.log')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

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


writePidFile()
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
            logger.info("{} {:.1f}".format(id, t))
            s = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
            timestamp =  s[:-3]

            if cfg['mqtt']['enabled'] == True:
                client.publish(cfg['mqtt']['topic'],  '{ "temperature_' + str(id) + '":"' + str(t) + '", "datetime":"' + str(timestamp) + '" }') # publish to mqtt
         else:
            logger.info("Temperature sensor error")

      except:
         pass


   try:
     # Print the values to the serial port
     temperature_c = dhtDevice.temperature
     temperature_f = temperature_c * (9 / 5) + 32
     humidity = dhtDevice.humidity
     logger.info(
        "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
             temperature_f, temperature_c, humidity
          )
      )
     if cfg['mqtt']['enabled'] == True:
          client.publish(cfg['mqtt']['topic'],  '{ "temperature_dht' +  '":"' + str(temperature_f) + '", "datetime":"' + str(timestamp) + '" }') # publish to mqtt
          client.publish(cfg['mqtt']['topic'],  '{ "humidity' +  '":"' + str(humidity) + '", "datetime":"' + str(timestamp) + '" }') # publish to mqtt
   except RuntimeError as error:
     # Errors happen fairly often, DHT's are hard to read, just keep going
     logger.info(error.args[0])




   time.sleep(1.0)
