#include <Arduino.h>
#include <EspMQTTClient.h>
#include <credentials.h>
#include <HardwareSerial.h>

HardwareSerial SerialInterconn(2);

EspMQTTClient client {
  SSID,
  PASSWD,
  BROKER,
  //MQTTUSR,
  //MQTTPWD,
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
  SerialInterconn.begin(115200, SERIAL_8N1, 16, 17);
  SerialInterconn.flush();
}

bool checkMqttCon(){
  return client.isMqttConnected();
}
bool checkWifiCon(){
  return client.isMqttConnected();
}

void clearSerialInterconn() {
  int x;
  while (x = SerialInterconn.available() > 0)
  {
     while (x--) SerialInterconn.read();
  }
}

void clientLoop() {
  client.loop();
}

void sendMqttMessage(char* topic, const char* msg){
  //Serial.println(msg);
  client.publish(topic, msg);
}

void sendSerialMessage(u_char msg) {
  SerialInterconn.write(msg);
  Serial.print("Message sent: 0x"); Serial.println(msg, HEX);
}

u_char checkSerialMessage() {
  if(SerialInterconn.available() >0) {
    u_char msg = SerialInterconn.read();
    //Serial.print("Message received: "); Serial.println(msg);
    return msg;
  }
  else
    return 0;
}