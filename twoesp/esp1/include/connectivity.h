#ifndef CONNECTIVITY_H
#define CONNECTIVITY_H

#include <Arduino.h>


void initWireless();
bool checkMqttCon();
bool checkWifiCon();
void clientLoop();
void sendMqttMessage(char* topic, const char* msg);
void sendSerialMessage(int16_t msg);
int16_t checkSerialMessage();


#endif