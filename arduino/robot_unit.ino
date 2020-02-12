#define DIR(x) ((x) < 0 ? HIGH : LOW)
#define	SGN(x) ((x) < 0 ? -1 : 1)

/*
SETTING: Pin values
*/
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
//
/*
SETTING: Robot data
*/
#define MODE_NONE 0
#define MODE_INIT 5
#define MODE_PATHLINE 1
#define MODE_PATHARC 2
#define MODE_PATHTURN 3
#define MODE_PATHVELOCITY 4

#define STATUS_INIT 0
#define STATUS_IDLE 1
#define STATUS_WORKING 2

uint8_t robotMode = MODE_NONE;
uint8_t robotStatus = STATUS_INIT;

#define ROBOTSTATE_LEN 3
#define ROBOTSENSOR_LER 1
#define ROBOTPARAM_LEN 4
#define PARAMETER_BYTE_LEN 4
/*
State array:
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
float robotState[ROBOTSTATE_LEN] = {};
float robotSensor[ROBOTSENSOR_LER] =   {};

const float robotParametersDefault[] = {0.0f, 92.0f, 21.0f, 21.0f};
/*
Parameters array:
0 - robot ID
1 - wheel distance [mm]
2 - left wheel radius [mm]
3 - right wheel radius [mm]
*/
float robotParameters[ROBOTPARAM_LEN] = {};
//
/*
SETTING: Message read
*/
#define BAUDRATE 9600
#define MSG_NONE 0
#define MSG_READ 1
#define MSG_END 2
#define MSG_ERROR 3
#define HEADER 42 //ASCII for '*'

#define MSG_BUFFERLEN 80

const size_t idxRobotID = 1;
const size_t idxRobotMode = 2;
const size_t idxMsgLen = 3;
const size_t msgModeLen = 3;

volatile size_t msgBufferIdx = 0;
volatile uint8_t msgBuffer[MSG_BUFFERLEN] = {};
//
/*
SETTING: Odometry
*/
#define K 75*3

volatile long wheelCounterLeft = 0;
volatile long wheelCounterRight = 0;
unsigned long timeSaved = 0;
unsigned long timeDelta = 10;

float wheelLeftOmega = 0;
float wheelRightOmega = 0;
float wheelLeftDistance = 0;
float wheelRightDistance = 0;
//
/*
SETTING: Velocity control
*/
#define WHEEL_VEL_LIMIT 1.0f
#define VEL_CONTROL_P 1.0
#define VEL_CONTROL_I 0.0

float errorLSum = 0.0f;
float errorRSum = 0.0f;

const unsigned long timeInit = 10000;
unsigned long timeTraveled = 0;
//
void setup() {
	pinMode(pinWheelLeftDir, OUTPUT);
	pinMode(pinWheelRightDir, OUTPUT);
	pinMode(pinWheelLeftSpeed, OUTPUT);
	pinMode(pinWheelRightSpeed, OUTPUT);

	pinMode(pinEncoderALeft, INPUT);
	pinMode(pinEncoderARight, INPUT);
	pinMode(pinEncoderBLeft, INPUT);
	pinMode(pinEncoderBRight, INPUT);

	attachInterrupt(digitalPinToInterrupt(pinEncoderALeft), encoderCounterLeft, RISING);
	attachInterrupt(digitalPinToInterrupt(pinEncoderARight), encoderCounterRight, RISING);

	setParameter();
	Serial.begin(BAUDRATE);
}

void loop() {
	switch (robotStatus) {
		case STATUS_INIT: 
		{
			if (millis() - timeTraveled > timeInit)
				robotStatus = STATUS_IDLE;
			break;
		}
		default: 
		{
			readMessage();
			setVelocities();
			odometry();
			break;
		}
	}
}

void setParameter() {
	for (size_t idx = 0; idx < ROBOTPARAM_LEN; idx++) {
		robotParameters[idx] = robotParametersDefault[idx];
	}
}

void encoderCounterLeft() {	
	//if (digitalRead(pinEncoderALeft) == HIGH) {
		if (digitalRead(pinEncoderBLeft) == LOW) 
			wheelCounterLeft--;
		else
			wheelCounterLeft++;
	/*} else {
		if (digitalRead(pinEncoderBLeft) == HIGH) 
			wheelCounterLeft--;
		else
			wheelCounterLeft++;
	}*/
}

void encoderCounterRight() {
	//if (digitalRead(pinEncoderARight) == HIGH) {
		if (digitalRead(pinEncoderBRight) == LOW) 
			wheelCounterRight++;
		else
			wheelCounterRight--;
	/*} else {
		if (digitalRead(pinEncoderBRight) == HIGH) 
			wheelCounterRight++;
		else
			wheelCounterRight--;
	}*/
}

void odometry() {
	unsigned long timeDiff = millis() - timeSaved;
	if (timeDiff >= timeDelta) {
		timeSaved = millis();
		timeTraveled += timeDiff;
		noInterrupts();
		//wheelLeftOmega = (float)wheelCounterLeft / (K * timeDiff) * 1000;
		//wheelRightOmega = (float)wheelCounterRight / (K * timeDiff) * 1000;
		float drL = 2 * PI * (float)wheelCounterLeft * robotParameters[2] / (K);
		float drR = 2 * PI * (float)wheelCounterRight * robotParameters[3] / (K);
		wheelCounterRight = 0;
		wheelCounterLeft = 0;
		interrupts();
		//float dr = (drL + drR) / 2;
		//float dfi = (drR - drL) / robotParameters[1];
		wheelLeftDistance += drL;
		wheelRightDistance += drR;
		//robotOrient += dfi;
		//robotDistance += dr;
		
	}	
}

float convertBytes2Float(uint8_t floatBytes[4]) {
	uint32_t value32 = 0;
	for (size_t idx = 0; idx < 4; idx++) {
		value32 |= ((uint32_t)floatBytes[3 - idx]) << (8 * idx);
	}
	return reinterpret_cast<float &>(value32);
}

bool checkMsg(uint8_t *msgToCheck, size_t length) {
	//size_t msgFullLen = msgToCheck[idxMsgLen] + msgModeLen;
	uint8_t modulo = 255;
	uint8_t sum = 0;
	for (size_t idx = 1; idx < length; idx++) {
		sum += msgToCheck[idx];
	}
	sum = modulo - sum;
	return sum == msgToCheck[length];
}

void flushBuffer(size_t idxStart, size_t length) {
	for (size_t idx = 0; idx < length; idx++)
		msgBuffer[(idxStart + idx) % MSG_BUFFERLEN] = 0;
}

void readMessage() {
	
	bool readNew = false;
	while (Serial.available() > 0) {
		msgBuffer[msgBufferIdx] = (uint8_t) Serial.read();
		msgBufferIdx = (msgBufferIdx + 1) % MSG_BUFFERLEN;
		readNew = true;
	}
	if (readNew) {
		bool msgNew;
		uint8_t msg[MSG_BUFFERLEN / 2] = {0};
		for (size_t idxHeader = 0; idxHeader < MSG_BUFFERLEN; idxHeader++) {
			
			msgNew = false;
			size_t len;
			if (msgBuffer[idxHeader] == HEADER) {
				len = msgBuffer[(idxHeader + idxMsgLen) % MSG_BUFFERLEN] + msgModeLen;
				for (size_t idxMsg = 0; idxMsg < len + 1; idxMsg++) {
					msg[idxMsg] = msgBuffer[(idxHeader + idxMsg) % MSG_BUFFERLEN];
				}
				msgNew = checkMsg(msg, len);
			}
			if (msgNew) {
				if (updateRobot(msg)) {
					flushBuffer(idxHeader, len);
					break;
				}
			}
		}
	}
}

void sendStatus() {
	Serial.println(robotStatus);
}

void resetRobotState() {
	robotMode = MODE_NONE;
	for (size_t idx = 0; idx < ROBOTSTATE_LEN; idx++) {
		robotState[idx] = 0.0f;
	}
}

bool updateRobot(uint8_t *msg) {
	
	switch (msg[idxRobotMode]) {
		case MODE_INIT: 
		{
			robotParameters[0] = (float) msg[idxRobotID];
			for (size_t idx = idxMsgLen + 1; idx < msg[idxMsgLen] - 1; idx += PARAMETER_BYTE_LEN + 1) {
				uint8_t buffer[PARAMETER_BYTE_LEN] = {};
				for (size_t idxByte = 0; idxByte < PARAMETER_BYTE_LEN; idxByte++) {
					buffer[idxByte] = msg[idx + idxByte + 1];
				}
				robotParameters[(size_t)msg[idx]] = convertBytes2Float(buffer);
			}
			return true;
		}

		default: 
		{
			if ((uint8_t)robotParameters[0] == msg[idxRobotID]) {
				robotMode = msg[idxRobotMode];
				for (size_t idx = idxMsgLen + 1; idx < msg[idxMsgLen] - 1; idx += PARAMETER_BYTE_LEN + 1) {
					uint8_t buffer[PARAMETER_BYTE_LEN] = {};
					for (size_t idxByte = 0; idxByte < PARAMETER_BYTE_LEN; idxByte++) {
						buffer[idxByte] = msg[idx + idxByte + 1];
					}
					robotState[(size_t)msg[idx]] = convertBytes2Float(buffer);
				}
				timeTraveled = 0;
				wheelLeftDistance = 0.0f;
				wheelRightDistance = 0.0f;
				return true;

			} else {
				return false;
			}
		}
	}
}

int trajectory(float distance, unsigned long timeFinal, float &velocity, float &distanceTraveled) {
	float velConst = 0.5f;
	float blend = 0.15f;
	float t = (float)timeTraveled / timeFinal;
	float velMax = distance / timeFinal / (1 - blend) / velConst;
	if (velMax > 1.0f)
		return 1;

	if (t < blend) {
		distanceTraveled = distance * ( t * t / 2 / blend ) / (1 - blend);
		velocity = velMax * ( t / blend );
		return 0;
	}
	if (t < 1.0f - blend) {
		distanceTraveled = distance * ( t - blend/2 ) / (1 - blend);
		velocity = velMax;
		return 0;
	} else 
	if (t < 1.0f) {
		distanceTraveled = distance * ( t - blend/2 - (t - 1 + blend)*(t - 1 + blend)/2/blend ) / (1 - blend);
		velocity = velMax * ( (1 - t) / blend );
		return 0;
	} else {
		distanceTraveled = distance * 1.0;
		velocity = 0.0f;
		return 1;
	}
}

void velocityControl(float& velocityL, float& velocityR, float goalDistL, float goalDistR) {
	float errorL = goalDistL - wheelLeftDistance;
	float errorR = goalDistR - wheelRightDistance;
	float _errorLSum = errorLSum + errorL;
	float _errorRSum = errorRSum + errorR;

	float _velocityL = errorL*VEL_CONTROL_P + _errorLSum*VEL_CONTROL_I; 
	float _velocityR = errorR*VEL_CONTROL_P + _errorRSum*VEL_CONTROL_I;

	if (abs(_velocityL) > WHEEL_VEL_LIMIT) {
		velocityL = errorL*VEL_CONTROL_P + errorLSum*VEL_CONTROL_I;
	} else {
		velocityL = _velocityL;
		errorLSum = _errorLSum;
	}

	if (abs(_velocityR) > WHEEL_VEL_LIMIT) {
		velocityR = errorR*VEL_CONTROL_P + errorRSum*VEL_CONTROL_I;
	} else {
		velocityR = _velocityR;
		errorRSum = _errorRSum;
	}
}

void setVelocities() {
	float velL, velR;
	float distFinL, distFinR, distL, distR;
	unsigned long timeF = (unsigned long) (robotState[0] * 1000);

	int errorCode = 0;

	switch (robotMode) {
		case MODE_NONE:
		{	
			velL = 0.0f;
			velR = 0.0f;
			break;
		}

		case MODE_PATHLINE:
		{
			distFinL = robotState[1];
			distFinR = distFinL;
			errorCode |= trajectory(distFinL, timeF, velL, distL);
			errorCode |= trajectory(distFinR, timeF, velR, distR);
			velocityControl(velL, velR, distL, distR);
			break;
		}
		case MODE_PATHARC:
		{
			distFinL = (robotState[2]-robotParameters[1]/2)*robotState[1];
			distFinR = (robotState[2]+robotParameters[1]/2)*robotState[1];
			errorCode |= trajectory(distFinL, timeF, velL, distL);
			errorCode |= trajectory(distFinR, timeF, velR, distR);
			velocityControl(velL, velR, distL, distR);
			break;
		}
		case MODE_PATHTURN:
		{
			distFinL = -robotState[1] * robotParameters[1]/2;
			distFinR = -distFinL;
			errorCode |= trajectory(distFinL, timeF, velL, distL);
			errorCode |= trajectory(distFinR, timeF, velR, distR);
			velocityControl(velL, velR, distL, distR);
			break;
		}
		case MODE_PATHVELOCITY:
		{
			if (timeTraveled < timeF) {
				velL = constrain(robotState[1], -WHEEL_VEL_LIMIT, WHEEL_VEL_LIMIT);
				velR = constrain(robotState[2], -WHEEL_VEL_LIMIT, WHEEL_VEL_LIMIT);
			} else {
				errorCode |= 1;
			}
			break;
		}
	}
	if (errorCode == 0) {
		digitalWrite(pinWheelLeftDir, DIR(velL));
		digitalWrite(pinWheelRightDir, DIR(velR));

		analogWrite(pinWheelRightSpeed, (int)abs(velR * 255));	
		analogWrite(pinWheelLeftSpeed, (int)abs(velL * 255));
		
	} else {
		robotMode = MODE_NONE;
	}
}