#include <Arduino.h>
#include <EspMQTTClient.h>
#include <credentials.h>
#include <HardwareSerial.h>

HardwareSerial Serial2(2);

EspMQTTClient client {
  SSID,
  PASSWD,
  BROKER,
  MQTTUSR,
  MQTTPWD,
  CLIENT_ID,
  PORT
};

void onConnectionEstablished(){
  Serial.println("ESP ONLINE");
}

void initWireless(){
  client.enableDebuggingMessages();
  client.setMaxPacketSize(20000);
  client.setMqttReconnectionAttemptDelay(10000);
  client.setWifiReconnectionAttemptDelay(15000);

  // Serial between esps
  Serial2.begin(9600, SERIAL_8N1, 16, 17);
}

bool checkMqttCon(){
  return client.isMqttConnected();
}
bool checkWifiCon(){
  return client.isMqttConnected();
}

void clientLoop() {
  client.loop();
}

void sendMqttMessage(char* topic, const char* msg){
  //Serial.println(msg);
  client.publish(topic, msg);
}

void sendSerialMessage(int16_t msg) {
  Serial2.write(msg);
}

int16_t checkSerialMessage() {
  if(Serial2.available() >= 1) {
    return Serial.read();
  }
  else
    return 0;
}