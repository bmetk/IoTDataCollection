import os

mqtt_addr = "mosquitto" #"mosquitto"
mqtt_port = 1883
mqtt_ws_port = 9001
mqtt_usr = os.environ["MQTT_USERNAME"]
mqtt_pwd = os.environ["MQTT_PASSWORD"]
mqtt_topic = "bmetk/markk/lathe/#"

analytics_topic = "bmetk/markk/lathe_analytics/vibration/backend"

influxhost = "http://influxdb:8086"
token = os.environ["INFLUX_TOKEN_OPENDAQ"] #"t1mA7xR5JLJMy_Ui6owQgP9njBrUUdjBG0cJmYmOc-9Igf0IMFCjRKcDVUbsKoivH7tCHy8ACF9xGbcXQGcbuw=="
org = "bmetk"
bucket = "opendaq"