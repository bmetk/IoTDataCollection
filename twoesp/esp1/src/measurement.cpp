#include <Arduino.h>
#include <cmath>
#include <Adafruit_MLX90614.h> // temperature
#include <connectivity.h>

#define TEMP_TOPIC "bmetk/markk/lathe/temperature/mlx90614/tempC"
#define RPM_TOPIC  "bmetk/markk/lathe/speed/m0c70t3/rpm"
#define AMP_TOPIC  "bmetk/markk/lathe/current/ampmeter/amp"


// Optocoupler
#define OPTO_PIN 36
#define HOLE_COUNT 6 // number of holes on the disk
// Current meter
#define PHASE1_PIN 32
#define PHASE2_PIN 33
#define PHASE3_PIN 35
#define OFFSET_PIN 34

Adafruit_MLX90614 mlx = Adafruit_MLX90614();

unsigned long currentTime = 0;
unsigned long previousTime = 0;


// measurement variables
const double resistor = 150.0; // 150 Ohm resistor connected to the coil
float rpm = 0;
volatile int holes;

// interrupt routine for rpm measurement
void IRAM_ATTR countHoles(){
    holes++;
}



//---------------------
// Initializing sensors
//---------------------
void setupSensors() {
    // Current meter setup
    pinMode(PHASE1_PIN, INPUT);
    pinMode(PHASE2_PIN, INPUT);
    pinMode(PHASE3_PIN, INPUT);
    pinMode(OFFSET_PIN, INPUT);
    
    // Optocoupler setup
    pinMode(OPTO_PIN, INPUT_PULLUP);
    attachInterrupt(OPTO_PIN, countHoles, FALLING);
    previousTime = millis();

    // Temperature sensor setup
    int retry = 0;
    while (retry < 10) {
        if (mlx.begin()) {
            break;  // Break out of the loop if initialization succeeds
        }
        retry++;
        delay(200);
    }
}


void setRPMTime() {
    previousTime = millis();
}


//----------------------------------------------------------
// Function for checking the state of the temperature sensor
//----------------------------------------------------------
bool checkTempSensor() {
    if(mlx.readAmbientTempC() > -10000) {
        return true;
    }
    else {
        mlx.begin();
        return false;
    }
}



//------------------------------------------------------------------
// Measurement functions for rpm, current draw and motor temperature
//------------------------------------------------------------------
const int sampleSize = 100;
double phase1Arr[sampleSize]; 
double phase2Arr[sampleSize]; 
double phase3Arr[sampleSize]; 
int measurementCount = 0;
// current
double readVoltage(int pin){
    return ((double(analogRead(pin))*3.3)/4095.0);
}

double voltsToAmps(double voltage, double offset){
    voltage -= offset;

    if(voltage < 0) {
        voltage *= -1;
    }
    
    return (voltage/resistor)*1000.0;
}

/*void getCurrent(){
    double offset = readVoltage(OFFSET_PIN);
    double phase_1 = voltsToAmps(readVoltage(PHASE1_PIN), offset);
    double phase_2 = voltsToAmps(readVoltage(PHASE2_PIN), offset);
    double phase_3 = voltsToAmps(readVoltage(PHASE3_PIN), offset);

    String current = String(phase_1) + ";" + String(phase_2) + ";" + String(phase_3);
    sendMqttMessage(AMP_TOPIC, current.c_str());
}*/

void getCurrent() {
    if(measurementCount < sampleSize) {
        double offset = readVoltage(OFFSET_PIN);
        phase1Arr[measurementCount] = voltsToAmps(readVoltage(PHASE1_PIN), offset);
        phase2Arr[measurementCount] = voltsToAmps(readVoltage(PHASE2_PIN), offset);
        phase3Arr[measurementCount] = voltsToAmps(readVoltage(PHASE3_PIN), offset);
        measurementCount++;
    }
}

double getRMS(double arr[]) {
    double squaredSum = 0.0f;
    for (int i = 0; i < sampleSize; ++i) {
        squaredSum += arr[i] * arr[i];
    }

    double meanSquared = squaredSum / static_cast<double>(sampleSize);
    double rms = sqrt(meanSquared);

    return rms;
}

void sendCurrent() {
    String current = String(getRMS(phase1Arr)) + ";" + String(getRMS(phase2Arr)) + ";" + String(getRMS(phase3Arr));
    sendMqttMessage(AMP_TOPIC, current.c_str());
    measurementCount = 0;
}



// RPM measurement
void getRpm() {
    currentTime = millis();
    rpm = (static_cast<float>(holes)/static_cast<float>(HOLE_COUNT)) * 60.0 / ((currentTime-previousTime)/1000.0);
    holes = 0;
    previousTime = currentTime;
    sendMqttMessage(RPM_TOPIC, String(rpm).c_str());
}



// Temperature measurement
void getTempC() {
    double tempC = mlx.readObjectTempC();
    if(tempC != NAN) {
        sendMqttMessage(TEMP_TOPIC, String(tempC).c_str());
    }
    else {
        sendMqttMessage(TEMP_TOPIC, String(-100).c_str());
    }
}

