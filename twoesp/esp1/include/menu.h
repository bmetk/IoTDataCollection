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
void processSerial(int16_t msg);


void firstLevel();


#endif