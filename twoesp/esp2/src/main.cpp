#include <Arduino.h>
#include "mpu6500.h"
#include "EspMQTTClient.h"
#include "ArduinoJson.h"
#include <HardwareSerial.h>



////////////////////////////////////////////////////////////////////////////////////////
//
//    Constants / Definitions
//
////////////////////////////////////////////////////////////////////////////////////////



#define VIBX_TOPIC "bmetk/markk/lathe/vibration/mpu9250/vibX"
#define VIBY_TOPIC "bmetk/markk/lathe/vibration/mpu9250/vibY"
#define VIBY_TOPIC "bmetk/markk/lathe/vibration/mpu9250/vibZ"
#define PORT       1883
#define DRDY_PIN   27
#define MPU_ADDR   0x68
#define WHOAMI_REG 0x75


EspMQTTClient client(
  "I40TK-office",//"vulcanus",
  "Ipar4Ir0d4",//"ketszersult",
  "172.22.101.1",
  "bmetk",
  "iot23",
  "kermarkesp",
  PORT
);


bfs::Mpu6500 imu;
HardwareSerial Serial2(2);


const size_t CAPACITY = JSON_ARRAY_SIZE(1024);
StaticJsonDocument<CAPACITY> docX;
StaticJsonDocument<CAPACITY> docY;
StaticJsonDocument<CAPACITY> docZ;


static constexpr float G_MPS2 = 9.80665f;
float accel_scale;
const int sampleSize = 1024;
bool DATA_READY = false;
bool READ = false;
bool enableCollection = true;
int intCounter = 0;
int idx = 0;


int16_t rawX[sampleSize];
int16_t rawY[sampleSize];
int16_t rawZ[sampleSize];
float vRealX[sampleSize];
float vRealY[sampleSize];
float vRealZ[sampleSize];


bool mpuOk = true, prevMpuOk;
bool clientOk = true, prevClientOk;
bool enableDiagnostics = false;
bool stateChange = false;


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

  Serial2.begin(9600, SERIAL_8N1, 16, 17);

  Wire.begin();
  Wire.setClock(400000);

  //WiFi and MQTT configuration
  //client.enableDebuggingMessages();
  client.setMaxPacketSize(20000);
  client.setMqttReconnectionAttemptDelay(10000);
  client.setWifiReconnectionAttemptDelay(15000);



  // Accelerometer configuration
  imu.Config(&Wire, bfs::Mpu6500::I2C_ADDR_PRIM); // default address is 0x68
  
  if (!imu.Begin()) {
    Serial.println("Error initializing communication with IMU");
    while(1) {}
  }
  // setting sample rate divider (0 is 1000Hz)
  if (!imu.ConfigSrd(0)) {
    Serial.println("Error configured SRD");
    while(1) {}
  }
  // enableing data ready interrupt for reading
  if (!imu.EnableDrdyInt()) {
    Serial.println("Error enableing data ready interrupt");
  }

  accel_scale = imu.accel_range()/32767.5f;

  pinMode(DRDY_PIN, INPUT_PULLUP);
  attachInterrupt(DRDY_PIN, onDataReady, RISING);


  // Waiting for connection
  while(!client.isConnected()) {
    delay(200);
    client.loop();
  }

  // sending initial health
  delay(2000);
  sendSerialMessage();
}


////////////////////////////////////////////////////////////////////////////////////////
//
//    Function declarations
//
////////////////////////////////////////////////////////////////////////////////////////



void collectData();
void decodeAccelData();
void sendJsonMessage();
void checkSystemHealth();
void sendSerialMessage();



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

  if(enableDiagnostics) {
    checkSerialMessage();
    checkSystemHealth();
    if(stateChange) {
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
  Wire.write(0x3B); // Start with register 0x3B (ACCEL_XOUT_H)
  Wire.endTransmission(false);
  Wire.requestFrom(bfs::Mpu6500::I2C_ADDR_PRIM, 2 , true/**/); // Read 6 registers total, each axis value is stored in 2 registers

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
    vRealY[i] = static_cast<float>(rawX[i]*accel_scale*G_MPS2);
    
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

    client.publish(VIBX_TOPIC, jsonStringX);
    client.publish(VIBY_TOPIC, jsonStringY);
    //client.publish(VIBZ_TOPIC, jsonStringZ);

    enableDiagnostics = true;
    //imu.EnableDrdyInt();
  } 
}



//----------------------------------------------
// Checking status of MPU and ESP client
//----------------------------------------------
void checkSystemHealth() {
  prevClientOk = clientOk;
  prevMpuOk = mpuOk;

  if(!client.isConnected()) {
    clientOk = true;
  }
  else {
    clientOk = false;
  }

  Wire.beginTransmission(MPU_ADDR); // Start communication with MPU6050
  Wire.write(WHOAMI_REG); // Send WHOAMI register address
  Wire.endTransmission(false); // Send restart signal to keep connection alive

  Wire.requestFrom(MPU_ADDR, 1); // Request one byte from MPU6050

  if (Wire.available()) { // Check if byte is available
    byte val = Wire.read(); // Read byte from MPU6050
    //Serial.println(val, HEX); // Print byte in hexadecimal format

    mpuOk = true;
  }
  else {
    mpuOk = false;
  }


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
//    - MPU UP             0x0F
//
//------------------------------------------------------------
void sendSerialMessage() {
  int msg = 0;

  if(mpuOk)
    msg += 0x0F;
  if(!mpuOk)
    msg += 0x08;

  if(enableCollection && clientOk)
    msg += 0x01;
  if(!clientOk)
    msg += 0x02;
  if(!enableCollection)
    msg += 0x04;
  
  Serial2.write(msg);
}



//----------------------------------
// Execute instructions sent by ESP1
//----------------------------------
void checkSerialMessage() {
  if(Serial2.available() >= 0){
    int16_t msg = Serial2.read();

    switch (msg) {
    case 0x01:
      enableCollection = !enableCollection;
      idx = 0;
      stateChange = true;
      //sendSerialMessage();
      break;
    
    case 0x02:
      ESP.restart();
      break;
    
    default:
      break;
    }
  }
}