#include <Arduino.h>
#include "mpu6500.h"
#include "EspMQTTClient.h"
#include "ArduinoJson.h"
#include <HardwareSerial.h>
#include "credentials.h"



////////////////////////////////////////////////////////////////////////////////////////
//
//    Constants / Definitions
//
////////////////////////////////////////////////////////////////////////////////////////



#define VIBX_TOPIC "bmetk/markk/lathe/vibration/mpu9250/vibX"
#define VIBY_TOPIC "bmetk/markk/lathe/vibration/mpu9250/vibY"
#define VIBZ_TOPIC "bmetk/markk/lathe/vibration/mpu9250/vibZ"

#define DRDY_PIN   27
#define MPU_ADDR   0x68
#define WHOAMI_REG 0x75


EspMQTTClient client(
  SSID,
  PWD,
  MQTT_ADDR,
  MQTT_USR,
  MQTT_PWD,
  "opendaq2",
  MQTT_PORT
);


bfs::Mpu6500 imu;
HardwareSerial SerialInterconn(2);


const size_t CAPACITY = JSON_ARRAY_SIZE(1024);
StaticJsonDocument<CAPACITY> docX;
StaticJsonDocument<CAPACITY> docY;
StaticJsonDocument<CAPACITY> docZ;


static constexpr float G_MPS2 = 9.80665f;
float accel_scale;
const int sampleSize =          1024;
bool DATA_READY =               false;
bool READ = false;
bool enableCollection =         false;
int intCounter =                0;
int idx =                       0;


int16_t rawX[sampleSize];
int16_t rawY[sampleSize];
int16_t rawZ[sampleSize];
float vRealX[sampleSize];
float vRealY[sampleSize];
float vRealZ[sampleSize];


bool mpuOk =             true, prevMpuOk;
bool clientOk =          true, prevClientOk;
bool enableDiagnostics = false;
bool stateChange =       false;



////////////////////////////////////////////////////////////////////////////////////////
//
//    Function declarations
//
////////////////////////////////////////////////////////////////////////////////////////



void collectData();
void decodeAccelData();
void sendJsonMessage();
void checkSystemHealth();
void checkSerialMessage();
void sendSerialMessage();

void clearSerialInterconn() {
  int x;
  while (x = SerialInterconn.available() > 0)
  {
     while (x--) SerialInterconn.read();
  }
}



////////////////////////////////////////////////////////////////////////////////////////
//
//    Setup / interrupts
//
////////////////////////////////////////////////////////////////////////////////////////



void IRAM_ATTR onDataReady() {
  READ = true;
  intCounter++;
}



void setup() {
  Serial.begin(115200);
  while(!Serial) {}

  Wire.begin();
  Wire.setClock(400000);

  // configuring MQTT and WiFi clients
  //client.enableDebuggingMessages();
  client.setMaxPacketSize(20000);
  client.setMqttReconnectionAttemptDelay(1000);
  client.setWifiReconnectionAttemptDelay(1000);



  // accelerometer configuration
  imu.Config(&Wire, bfs::Mpu6500::I2C_ADDR_PRIM); // default address is 0x68
  
  if (!imu.Begin()) {
    Serial.println("Error initializing communication with IMU");
    //while(1) {}
  }

  // setting sample rate divider (0 is 1000Hz)
  if (!imu.ConfigSrd(0)) {
    Serial.println("Error configured SRD");
    //while(1) {}
  }

  // setting acceleration range to 4g
  imu.ConfigAccelRange(bfs::Mpu6500::ACCEL_RANGE_4G);

  // enableing data ready interrupt for reading
  if (!imu.EnableDrdyInt()) {
    Serial.println("Error enableing data ready interrupt");
  }

  accel_scale = imu.accel_range()/32767.5f;

  // interrupt
  pinMode(DRDY_PIN, INPUT_PULLUP);
  attachInterrupt(DRDY_PIN, onDataReady, RISING);


  // Waiting for connection
  while(!client.isConnected()) {
    delay(200);
    client.loop();
  }

  // sending initial health
  delay(2000);

  // starting serial connection between ESPs
  SerialInterconn.begin(115200, SERIAL_8N1, 16, 17);
  clearSerialInterconn();
  sendSerialMessage();
}






////////////////////////////////////////////////////////////////////////////////////////
//
//    Loop section
//
////////////////////////////////////////////////////////////////////////////////////////



void loop() {
  
  client.loop();

  if(enableCollection) {
    sendJsonMessage();
  }
  else if (!enableCollection) {
    enableDiagnostics = true;
  }

  if(enableDiagnostics || !mpuOk) {
    checkSerialMessage();
    checkSystemHealth();
    if(stateChange) {
      Serial.println("Sending system health update");
      sendSerialMessage();
      stateChange = false;
    }

    enableDiagnostics = false;
    imu.EnableDrdyInt();
  }
}



////////////////////////////////////////////////////////////////////////////////////////
//
//    Function definitions
//
////////////////////////////////////////////////////////////////////////////////////////



//-------------------------------------------------
// ESP client connection callback
//-------------------------------------------------
void onConnectionEstablished() {
  Serial.println("Connected to broker.");
}



//-------------------------------------------------
// MPU6500 data collection
//-------------------------------------------------
void collectData() {
  Wire.beginTransmission(bfs::Mpu6500::I2C_ADDR_PRIM);
  Wire.write(0x3B); // start with register 0x3B (ACCEL_XOUT_H)
  int transmissionResult = Wire.endTransmission(false);

  if (transmissionResult != 0) {
    // I2C connection failed, set enableDiagnostics to true
    enableDiagnostics = true;
    return;
  }

  int bytesRead = Wire.requestFrom(bfs::Mpu6500::I2C_ADDR_PRIM, 6, true); // read 6 registers total, each axis value is stored in 2 registers

  if (bytesRead != 6) {
    // I2C connection failed, set enableDiagnostics to true
    enableDiagnostics = true;
    return;
  }

  rawX[idx] = static_cast<int16_t>(Wire.read() << 8 | Wire.read());
  rawY[idx] = static_cast<int16_t>(Wire.read() << 8 | Wire.read());
  rawZ[idx] = static_cast<int16_t>(Wire.read() << 8 | Wire.read());
  

  idx++;
  READ = false;


  if(idx >= sampleSize){
    imu.DisableDrdyInt();
    DATA_READY = true;
  }
}



//-----------------------------------------------------
// Converting the integer values to real vibration data
//-----------------------------------------------------
void decodeAccelData() {
  for(uint16_t i=0; i<sampleSize; i++) {
    vRealX[i] = static_cast<float>(rawX[i]*accel_scale*G_MPS2);
    vRealY[i] = static_cast<float>(rawY[i]*accel_scale*G_MPS2);
    vRealZ[i] = static_cast<float>(rawZ[i]*accel_scale*G_MPS2);
    
  }
}



//----------------------------------------------
// Encoding the vibration data and publishing it
//----------------------------------------------
void sendJsonMessage(){
  if(!DATA_READY && READ){
    // start collecting data
    collectData();
  }
  else if(DATA_READY){
    // stop collecting data
    imu.DisableDrdyInt();

    // reset variables and flags
    DATA_READY = false;
    intCounter = 0;
    READ = false;
    idx = 0;
    
    // decode all collected data
    decodeAccelData();

    // convert the float array to Json
    JsonArray arrayX = docX.to<JsonArray>();
    JsonArray arrayY = docY.to<JsonArray>();
    JsonArray arrayZ = docZ.to<JsonArray>();

    for(uint16_t i = 0; i < sampleSize; i++) {
      arrayX.add(vRealX[i]);
      arrayY.add(vRealY[i]);
      arrayZ.add(vRealZ[i]);
    }

    // serialization and publishing
    String jsonStringX;
    String jsonStringY;
    String jsonStringZ;
    serializeJson(docX, jsonStringX);
    serializeJson(docY, jsonStringY);
    serializeJson(docZ, jsonStringZ);

    SerialInterconn.write(0xAA); // code for data publishing

    client.publish(VIBX_TOPIC, jsonStringX);
    client.publish(VIBY_TOPIC, jsonStringY);
    client.publish(VIBZ_TOPIC, jsonStringZ);
    Serial.println("Accel data published to broker");

    enableDiagnostics = true;
  }
}



//----------------------------------------------
// Checking status of MPU and ESP client
//----------------------------------------------
void checkSystemHealth() {
  prevClientOk = clientOk;
  prevMpuOk = mpuOk;

  // checking client state
  clientOk = client.isConnected();
  
  // checking MPU state via WHOAMI register
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(WHOAMI_REG);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 1);

  if (Wire.available()) {
    byte val = Wire.read();
    mpuOk = true;
  }
  else {
    mpuOk = false;
    idx = 0;
  }

  // if there was a change, update the state of the system
  if(clientOk != prevClientOk || mpuOk != prevMpuOk)
    stateChange = true;
}



//------------------------------------------------------------
// Sending messages to ESP1
//
// Codes:
//    - ONLINE             0x01
//    - OFFLINE (error)    0x02
//    - OFFLINE (manula)   0x04
//    - MPU DOWN           0x08
//    - MPU UP             0x10
//
//------------------------------------------------------------
void sendSerialMessage() {
  u_char msg = 0;
  Serial.println("Sending system health: ");
  
  if(enableCollection && clientOk) {
    msg += 0x01;
    Serial.print("ONLINE, ");
  }
  if(!clientOk) {
    msg += 0x02;
    Serial.print("OFFLINE (ERR), ");
  }
  if(!enableCollection) {
    msg += 0x04;
    Serial.print("OFFLINE (MANUAL), ");
  }
  if(!mpuOk) {
    msg += 0x08;
    Serial.print("MPU DOWN, ");
  }
  if(mpuOk) {
    msg += 0x10;
    Serial.print("MPU UP, ");
  }

  SerialInterconn.write(msg);
}



//----------------------------------
// Execute instructions sent by ESP1
//----------------------------------
void checkSerialMessage() {
  if(SerialInterconn.available() > 0){
    u_char msg = SerialInterconn.read();

    switch (msg) {
    case 0x01:
      enableCollection = !enableCollection;
      idx = 0;
      stateChange = true;
      break;
    
    case 0x02:
      Serial.println("Restarting ESP2");
      ESP.restart();
      break;
    
    default:
      break;
    }
  }
}