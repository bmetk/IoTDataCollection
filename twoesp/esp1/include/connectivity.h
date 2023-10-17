#ifndef CONNECTIVITY_H
#define CONNECTIVITY_H

#include <Arduino.h>


void initWireless();
bool checkMqttCon();
bool checkWifiCon();
void clientLoop();
void sendMqttMessage(char* topic, const char* msg);
void sendSerialMessage(u_char msg);
u_char checkSerialMessage();
void clearSerialInterconn();

#endif