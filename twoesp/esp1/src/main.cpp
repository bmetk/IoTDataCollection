/*

  This version runs on a single esp32 with 4 sensors, a display and navigation buttons
  
  The sensors are:
    - MPU9250 vibration sensor
    - optocouler
    - temperature sensor
    - current meter

  The current diplay is a 0.92" 128x64 oled display.

  The two navigation buttons are:
    - Next: going to the next possinle state
    - Select: entering a new state/calling a function

  To utilise the two cores, both are running a task:
    - Task 1: display, mqtt etc.
    - Task 2: data collection

*/



#include <Arduino.h>
#include <menu.h>
#include <measurement.h>
#include <connectivity.h>
#include <parameters.h>



////////////////////////////////////////////////////////////////////////////////////////
//
//    Constants / Definitions
//
////////////////////////////////////////////////////////////////////////////////////////



TaskHandle_t Task1;
TaskHandle_t Task2;


#define NEXT_PIN 19
#define ENTER_PIN 18
volatile bool nextPressed = false;
volatile bool enterPressed = false;
unsigned long buttonTime = 0;
unsigned long lastButtonTime = 0;
const int debounceInteval = 250; // 250ms for button debouncing
unsigned long previousMillis;
const unsigned int measurementInterval = 2000;

////////////////////////////////////////////////////////////////////////////////////////
//
//    Function definitions
//
////////////////////////////////////////////////////////////////////////////////////////


//------------------------
// Handling button presses
//------------------------
void IRAM_ATTR nextOnPress() {
  buttonTime = millis();
  if(buttonTime - lastButtonTime > debounceInteval){
    nextPressed = true;
    lastButtonTime = buttonTime;
  }
}

void IRAM_ATTR enterOnPress() {
  buttonTime = millis();
  if(buttonTime - lastButtonTime > debounceInteval){
    enterPressed = true;
    lastButtonTime = buttonTime;
  }
}


//----------------------------------------------
// Function for Task1 - handling the menu system
//----------------------------------------------
void Task1code(void * pvParameters){
  for(;;){
    if(nextPressed) {
      updateState("next");
      nextPressed = false;
      Serial.println("next");
    }
    else if(enterPressed) {
      updateState("enter");
      enterPressed = false;
      Serial.println("enter");
    }
    //clientLoop();
    processSerial(checkSerialMessage());
    
    vTaskDelay(10);
  }
}


//------------------------------------------------------------
// Function for Task2 - reading sensor data and sending it out
//------------------------------------------------------------
void Task2code(void * pvParameters){
  while(!checkMqttCon()){
    delay(200);
    
    clientLoop();
  }
  previousMillis = millis();
  
  for(;;){

    if(millis() - previousMillis > measurementInterval && isCollectionEnabled()){
      getCurrent();
      getRpm();
      //getTempC();
      Serial.println("task2 done");
      previousMillis = millis();
    }
    
    clientLoop();
    vTaskDelay(10);
  }
}



////////////////////////////////////////////////////////////////////////////////////////
//
//    Setup
//
////////////////////////////////////////////////////////////////////////////////////////


void setup() {
  Serial.begin(115200);
  
  // Starting up the sensors and the wireless connection
  initWireless();
  setupSensors();

  // setting up the display
  setupDisplay();
  firstLevel();


  pinMode(NEXT_PIN, INPUT_PULLUP);
  pinMode(ENTER_PIN, INPUT_PULLUP);
  pinMode(DRDY_PIN, INPUT_PULLDOWN);

  attachInterrupt(NEXT_PIN, nextOnPress, FALLING);
  attachInterrupt(ENTER_PIN, enterOnPress, FALLING);



  xTaskCreatePinnedToCore(
                    Task1code,   /* Task function. */
                    "Task1",     /* name of task. */
                    10000,       /* Stack size of task */
                    NULL,        /* parameter of the task */
                    2,           /* priority of the task */
                    &Task1,      /* Task handle to keep track of created task */
                    1);          /* pin task to core 0 */                  
  delay(500); 

  //create a task that will be executed in the Task2code() function, with priority 1 and executed on core 1
  xTaskCreatePinnedToCore(
                    Task2code,   /* Task function. */
                    "Task2",     /* name of task. */
                    12000,       /* Stack size of task */
                    NULL,        /* parameter of the task */
                    1,           /* priority of the task */
                    &Task2,      /* Task handle to keep track of created task */
                    0);          /* pin task to core 1 */
  delay(500);

  //vTaskSuspend(Task2);
}

void loop() {
  // put your main code here, to run repeatedly:
}