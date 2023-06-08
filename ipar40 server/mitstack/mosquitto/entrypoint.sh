#!/bin/sh


PASSWDFILE=/mosquitto/config/passwordfile.txt
mosquitto_passwd -b $PASSWDFILE $MQTT_USERNAME $MQTT_PASSWORD

exec "$@"
