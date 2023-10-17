#include <Arduino.h>
#include <Adafruit_MLX90614.h> // temperature
#include <connectivity.h>

// MQTT definitions

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
const int resistor = 100; // 100 Ohm resistor connected to the coil
float rpm = 0;
volatile int holes;

// interrupt
void countHoles(){
    holes++;
}


void setupSensors() {
    // Current meter setup
    pinMode(PHASE1_PIN, INPUT);
    pinMode(PHASE2_PIN, INPUT);
    pinMode(PHASE3_PIN, INPUT);
    pinMode(OFFSET_PIN, INPUT);
    
    // Optocoupler setup
    pinMode(OPTO_PIN, INPUT_PULLUP);
    attachInterrupt(OPTO_PIN, countHoles, FALLING);

    // Temperature sensor setup
    
    if (!mlx.begin()) {
        int retry = 0;

        while(retry < 10) {
            if (!mlx.begin()) {
                retry++;
                delay(200);
            }
            else
                break;
        }

        if(retry >= 10) {
            // set the menu correspondingly
        }
    }

    previousTime = millis();
}

bool checkTempSensor() {
    if(mlx.readAmbientTempC() != NAN) {
        return true;
    }
    else {
        mlx.begin();
        return false;
    }
}


// Current measurement
double readVoltage(int pin){
    return (analogRead(pin)/4096*3.3);
}


double voltsToAmps(double voltage, double offset){
    voltage -= offset;
    double amps = (voltage/resistor)*1000;
    return amps;
}

void getCurrent(){
    double offset = analogRead(OFFSET_PIN);
    double phase_1 = voltsToAmps(readVoltage(PHASE1_PIN), offset);
    double phase_2 = voltsToAmps(readVoltage(PHASE2_PIN), offset);
    double phase_3 = voltsToAmps(readVoltage(PHASE3_PIN), offset);

    String current = String(phase_1) + ";" + String(phase_2) + ";" + String(phase_3);
    sendMqttMessage(AMP_TOPIC, current.c_str());
}

// RPM measurement
void getRpm() {
    currentTime = millis();
    rpm = (holes/HOLE_COUNT) * 60 / ((currentTime-previousTime)/1000.0);
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
}

