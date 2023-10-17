#ifndef MENU_H
#define MENU_H

#include <Arduino.h>


void updateState(char* btnId="");
void setupDisplay();
void printTabHeader(String title="");
void homeTab();
void errorTab(/*bool nextPage = false*/);
void settingsTab();
void drawCursor(int idx);
bool isCollectionEnabled();
void processSerial(u_char msg);
bool checkSendMeasurements();
void resetSendMeasurements();
String checkEsp2State();
void setErrorEnable(int index, int value);

void firstLevel();


#endif