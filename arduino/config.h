#ifndef CONFIG_H
#define CONFIG_H

#define DIR(x) ((x) < 0 ? HIGH : LOW)
#define	SGN(x) ((x) < 0 ? -1 : 1)

//Pins

const uint8_t pinEncoderALeft = 3;
const uint8_t pinEncoderBLeft = 5;
const uint8_t pinEncoderARight = 2;
const uint8_t pinEncoderBRight = 6;
const uint8_t pinWheelLeftDir = 7;
const uint8_t pinWheelRightDir = 8;
const uint8_t pinWheelLeftSpeed = 9;
const uint8_t pinWheelRightSpeed = 10;

const uint8_t pinPotentiometer = A5;
const uint8_t pinButton = 4;

//Robot operation mode codes

#define MODE_NONE 0
#define MODE_INIT 5
#define MODE_PATHLINE 1
#define MODE_PATHARC 2
#define MODE_PATHTURN 3
#define MODE_PATHVELOCITY 4

//Robot status codes 

#define STATUS_INIT 0
#define STATUS_IDLE 1
#define STATUS_WORKING 2
#define STATUS_ERROR 3

//Message transfer const

#define BAUDRATE 9600
#define MSG_HEADER 42 //ASCII for '*'
#define MSG_BUFFERLEN 80
#define PARAMETER_BYTE_LEN 4

//Odometry calculation const

const float paramsDefault[] = {92.0f, 21.0f, 21.0f, 0.0f, 0.0f, 0.0f};
#define K 75*3
#define VEL_LIMIT 1.0f

//Robot data buffer lengths
/*
Settings array:
0 - time [s]
MODE_PATHLINE:
	1 - distance [mm]
MODE_PATHTURN:
	1 - angle distance [rad]
MODE_PATHARC:
	1 - angle distance [rad]
	2 - arc radius [mm]
MODE_PATHVELOCITY:
	1 - left wheel velocity (-1.0 to 1.0)
	2 - right wheel velocity (-1.0 to 1.0)
*/
#define ROBOTSETTINGS_LEN 3

/*
Sensors array:
0 - distance sensor
*/
#define ROBOTSENSORS_LEN 1

/*
Parameters array:
0 - wheel distance [mm]
1 - left wheel radius [mm]
2 - right wheel radius [mm]
3 - velocity controller constant - Proportional part
4 - velocity controller constant - Integral part
5 - velocity controller constant - Differential part
*/
#define ROBOTPARAMS_LEN 7

#endif