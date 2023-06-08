import paho.mqtt.client as mqtt
import random
import time
import json

broker_address = "localhost"
broker_port = 1883
topic1 = "bmetk/mark/lathe/temperature/mlx90614/tempC"
topic2 = "bmetk/peti/lathe/speed/opto/rpm"
topic3 = "bmetk/markk/lathe/vibration/mpu9250/vibX"
topic4 = "bmetk/esp2/jsondemo"


client_id = f"python-mqtt-{random.randint(0, 1000)}"
client = mqtt.Client(client_id=client_id)
client.username_pw_set("bmetk", "iot23")
client.connect(broker_address, broker_port)

client.loop_start()

while True:

    
    data = {}
    magnitude = []

    magnitude = [round(random.uniform(0, 100), 2) for _ in range(1024)]

    data["magnitude"] = magnitude


    json_data = json.dumps(data)
    #print(json_data)


    random_int = random.randint(0, 100)
    client.publish(topic1, random_int)
    client.publish(topic2, random_int+100)
    client.publish(topic3, json_data)
    time.sleep(5)
