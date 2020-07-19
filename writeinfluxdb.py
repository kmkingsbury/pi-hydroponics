import glob
import time
import os, sys
import logging
import yaml
import datetime
import json
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient



def on_connect(client, userdata, flags, rc):  # The callback for when the client connects to the broker
    print("Connected with result code {0}".format(str(rc)))  # Print result of connection attempt
    client.subscribe(cfg['mqtt']['topic'])  # Subscribe to the topic “digitest/test1”, receive any messages published on it
    print("Subscribed to: " + cfg['mqtt']['topic'])  # Print result of connection attempt

def on_message(client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
    print("Message received-> " + msg.topic + " " + str(msg.payload))  # Print a received msg
    m_decode=str(msg.payload.decode("utf-8","ignore"))
#    print("data Received type",type(m_decode))
#    print("data Received",m_decode)
#    print("Converting from Json to Object")
    data=json.loads(m_decode) #decode json data
    print(type(data))
    print("JSON:" + str(data))
    timestamp = data["datetime"]
    measurement = '' 
    field = ''
    tag = ''
    prefix = "temperature_"
    sensorId = ''
    for key in data.keys():
        #print("key:" + key )
        if key.startswith(prefix):
            measurement = 'temperature'
            #print("temp")
            k =  key.lstrip(prefix)
            #print("test:" + k)
            #print("CFG?:"  + str(cfg['climate']))
            tag = cfg['climate'][k]
            field = data[key]
            sensorId = k
            #print("T&f:" + str(tag) + " - " + str(field))
        elif key == "humidity":
            measurement = 'humidity'
            #print("humidity")
            # this is Humidity
            tag = "humidity"
            field = data[key]
            sensorId = 'dht11'
        print ("tag:" + tag + " " + "field:" + field)
        json_body = [{
            "measurement": measurement,
            "tags": {
                "sensorlocation": tag,
                "sensorId": sensorId
            },
            "timestamp": timestamp.replace(" ","T") + "Z",
            "fields": {
                'value': float(field)
            }
        }]
        print("JB:"+ str(json_body))
        try:
            influxclient.write_points(json_body)
        except exceptions.InfluxDBClientError:
            print('Error saving event "%s" to InfluxDB', json_body)
        #print("res:" + str(r))

def writePidFile():
    pid = str(os.getpid())
    currentFile = open('/tmp/writeinfluxdb.pid', 'w')
    currentFile.write(pid)
    currentFile.close()


#logging.basicConfig(level=logging.INFO, format=' %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('writeinfluxdb')
logger.setLevel(logging.INFO)

fh = logging.FileHandler('./writeinfluxdb.log')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

writePidFile()

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

influxclient = InfluxDBClient(host=cfg['influxdb']['host'], port=cfg['influxdb']['port'])
influxclient.switch_database(cfg['influxdb']['dbname'])
# client.create_database('writetest')


# Setup MQTT
client = mqtt.Client("writeinfluxdb") #create new instance
# Loop start: These functions implement a threaded interface to the network loop. Calling loop_start() once, before or after connect*(), runs a thread in the background to call loop() automatically. This frees up the main thread for other work that may be blocking.
#client.loop_start()
client.on_connect = on_connect  # Define callback function for successful connection
client.on_message = on_message  # Define callback function for receipt of a message
# client.connect("m2m.eclipse.org", 1883, 60)  # Connect to (broker, port, keepalive-time)
client.connect(cfg['mqtt']['host']) #connect to broker
client.loop_forever()  # Start networking daemon
while True:
    sleep(0.01)
