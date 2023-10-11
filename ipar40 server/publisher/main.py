import paho.mqtt.client as mqtt
import random
import time
import json

broker_address = "152.66.34.82" #"152.66.34.82" #172.22.101.1"
broker_port = 61111 #61111 #1883
topic1 = "bmetk/markk/lathe/temperature/mlx90614/tempC"
topic2 = "bmetk/markk/lathe/speed/opto/rpm"
topic3 = "bmetk/markk/lathe/current/diy/cur"
topic4 = "bmetk/markk/lathe/vibration/mpu9250/vibX"
topic5 = "bmetk/markk/lathe/vibration/mpu9250/vibY"
topic6 = "bmetk/markk/lathe/vibration/mpu9250/vibZ"


client_id = f"python-mqtt-{random.randint(0, 1000)}"
client = mqtt.Client(client_id="pathon-mqtt-001")
client.username_pw_set("bmetk", "iot23")
client.connect(broker_address, broker_port)

client.loop_start()


def magnitude():
    mag = [str(round(random.uniform(0, 100), 2)) for _ in range(1024)]
    result = "[" + ', '.join(mag) + "]"

    return result


while True:

    
    magnitude_data = {}
    current_data = {}
    current = []
    current = [str(random.randint(0, 10)) for _ in range(3)]
    
    current = "[" + ', '.join(current) + "]"

    rpm = random.randint(0, 2500)
    tempC = random.randint(22, 70)
    
    client.publish(topic1, tempC)
    client.publish(topic2, rpm)
    client.publish(topic3, current)
    client.publish(topic4, magnitude())
    client.publish(topic5, magnitude())
    client.publish(topic6, magnitude())

    print("payloads sent")

    time.sleep(2)
