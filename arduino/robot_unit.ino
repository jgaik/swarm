#define sgn(x) ((x) < 0 ? LOW : HIGH)
#define BAUDRATE 9600

const uint8_t pinEncoderALeft = 2;
const uint8_t pinEncoderBLeft = 5;
const uint8_t pinEncoderARight = 3;
const uint8_t pinEncoderBRight = 6;
const uint8_t pinWheelLeftDir = 7;
const uint8_t pinWheelRightDir = 8;
const uint8_t pinWheelLeftSpeed = 9;
const uint8_t pinWheelRightSpeed = 10;

const uint8_t pinPotentiometer = A5;
const uint8_t pinButton = 4;

volatile int wheelCounterLeft = 0;
volatile int wheelCounterRight = 0;
unsigned long timeSaved = 0;
unsigned long timeDelta = 50;
unsigned long timeLastDebounce = 0;

#define WHEEL_RADIUS 21
#define WHEEL_DIST 89
#define WHEEL_VEL_LIMIT 400
#define K 75*12
#define VELCONTROL_P 100
float wheelLeftOmega = 0;
float wheelRightOmega = 0;
float robotPosX = 0;
float robotPosY = 0;
float robotOrient = 0;
float distanceTraveled = 0;

#define MSG_NONE 0
#define MSG_READ 1
#define MSG_END 2
#define MSG_ERROR 3
#define HEADER '*'

#define MODE_NONE 0
#define MODE_PATHLINE 1
#define MODE_PATHARC 2
#define MODE_PATHVELOCITY 3

#define BUFFERLEN_MSG 20

const size_t idxRobotID = 0;
const size_t idxRobotMode = 1;
const size_t idxMsgLen = 2;
const size_t idxParamStart = 3;
const size_t msgModeLen = 3;

int readStatus = MSG_NONE;
size_t msgReadCount = 0;
uint8_t msgBuffer[BUFFERLEN_MSG] = {};

uint8_t robotMode = MODE_NONE;
uint8_t robotStatus;

#define ROBOTSTATE_LEN 3
#define ROBOTSENSOR_LER 1
#define PARAMETER_BYTE_LEN 4
uint8_t robotState[ROBOTSTATE_LEN][PARAMETER_BYTE_LEN] = {};
uint8_t robotSensor[ROBOTSENSOR_LER][PARAMETER_BYTE_LEN] ={};

uint8_t buttonState;
uint8_t buttonStateLast = LOW;

void setup() {
	pinMode(pinWheelLeftDir, OUTPUT);
	pinMode(pinWheelRightDir, OUTPUT);
	pinMode(pinWheelLeftSpeed, OUTPUT);
	pinMode(pinWheelRightSpeed, OUTPUT);
	pinMode(pinButton, INPUT);
	pinMode(pinPotentiometer, INPUT);

	attachInterrupt(digitalPinToInterrupt(pinEncoderALeft), encoderCounterLeft, CHANGE);
	attachInterrupt(digitalPinToInterrupt(pinEncoderARight), encoderCounterRight, CHANGE);
	Serial.begin(BAUDRATE);
	digitalWrite(pinWheelLeftDir, HIGH);
	digitalWrite(pinWheelRightDir, HIGH);
}

void loop() {
	readCommand();
	changeRobotState();
	checkButton();
	setVelocities();
	calculateParams();
}

void checkButton() {
	uint8_t reading = digitalRead(pinButton);
	noInterrupts();
	if (reading != buttonStateLast) {
		timeLastDebounce = millis();
	}

	if ( (millis() - timeLastDebounce) > timeDelta ) {
		if (reading != buttonState) {
			buttonState = reading;
			if (buttonState == HIGH) {
				resetRobotState();
			}
		}
	}
	interrupts();
}

void encoderCounterLeft() {
	int chA = digitalRead(pinEncoderALeft);
	int chB = digitalRead(pinEncoderBLeft);
	if ( (chA == HIGH && chB == HIGH) || (chA == LOW && chB == LOW) )
		wheelCounterLeft--;
	else
		wheelCounterLeft++;
}

void encoderCounterRight() {
	int chA = digitalRead(pinEncoderARight);
	int chB = digitalRead(pinEncoderBRight);
	if ( (chA == HIGH && chB == HIGH) || (chA == LOW && chB == LOW) )
		wheelCounterRight++;
	else
		wheelCounterRight--;
}

void calculateParams() {
	if (millis() - timeSaved >= timeDelta) {
		timeSaved = millis();
		noInterrupts();
		wheelLeftOmega = wheelCounterLeft / (K * timeDelta);
		wheelRightOmega = wheelCounterRight / (K * timeDelta);
		float drL = 2 * PI * wheelCounterLeft * WHEEL_RADIUS / K;
		float drR = 2 * PI * wheelCounterRight * WHEEL_RADIUS / K;
		float dr = (drL + drR) / 2;
		float dfi = (drL - drR) / WHEEL_DIST;
		switch (robotMode) {
			case MODE_PATHLINE:
				distanceTraveled += dr;
				break;
			case MODE_PATHARC:
				distanceTraveled += abs(dfi);
				break;
			default:
				robotOrient += dfi;
				robotPosX += dr * cos(robotOrient);
				robotPosY += dr * sin(robotOrient);
				break;
		}
		wheelCounterRight = 0;
		wheelCounterLeft = 0;
		interrupts();
		//Serial.println("x: " + (String)robotPosX + " y: " + (String)robotPosY + " orient: " + (String)robotOrient);
	}	
}

float convertBytes2Float(uint8_t floatBytes[4]) {
	uint32_t value32 = 0;
	for (size_t idx = 0; idx < 4; idx++) {
		value32 |= ((uint32_t)floatBytes[3 - idx]) << (8 * idx);
	}
	return reinterpret_cast<float &>(value32);
}

bool checkMsg() {
	size_t msgFullLen = msgBuffer[idxMsgLen] + msgModeLen;
	int modulo = 256;
	uint8_t sum = 0;
	for (size_t idx = 0; idx < msgFullLen - 1; idx++) {
		sum += msgBuffer[idx];
	}
	sum = modulo - sum - 1;
	return sum == msgBuffer[msgFullLen - 1];
}

void flushBuffer() {
	for (size_t idx = 0; idx < BUFFERLEN_MSG; idx++)
		msgBuffer[idx] = 0;
}

void readCommand() {
	while (Serial.available() > 0) {
		char readSymbol = Serial.read();
		switch (readStatus) {
			case MSG_NONE:
				if (readSymbol == HEADER)
					readStatus = MSG_READ;
				break;
			case MSG_READ:
				if (msgReadCount < msgBuffer[idxMsgLen] + msgModeLen) {
					msgBuffer[msgReadCount] = (uint8_t)readSymbol;
					msgReadCount++;
				} else {
					if (checkMsg())
						readStatus = MSG_END;
					else
						readStatus = MSG_ERROR;
					
					msgReadCount = 0;
				}
			break;
		default:
			break;
		}
	}
}

void resetRobotState() {
	robotMode = MODE_NONE;
	for (size_t idx = 0; idx < ROBOTSTATE_LEN; idx++) {
		for (size_t idxByte = 0; idxByte < PARAMETER_BYTE_LEN; idxByte++) {
				robotState[idx][idxByte] = 0;
			}
	}
}

void changeRobotState() {
	if (readStatus == MSG_END) {
		Serial.println("[Arduino Robot]: New msg read");
		robotMode = msgBuffer[idxRobotMode];
		for (size_t idx = 0; idx < msgBuffer[idxMsgLen] - 1; idx += PARAMETER_BYTE_LEN + 1) {
			for (size_t idxByte = 0; idxByte < PARAMETER_BYTE_LEN; idxByte++) {
				robotState[(size_t)msgBuffer[idx + idxParamStart]][idxByte] = msgBuffer[idx + idxParamStart + idxByte + 1];
			}
		}
		String param_status = "";
		Serial.print("[Arduino Robot]: Robot parameters set: ");
		for (size_t idx = 0; idx < ROBOTSTATE_LEN; idx++) {
			param_status += (String)idx + ": " + (String)convertBytes2Float(robotState[idx]) + " ";
		}
		Serial.println(param_status);
		flushBuffer();
		readStatus = MSG_NONE;
	}
}

float velocityControl(float velocitySet, float distGoal) {
	float distError = distGoal - distanceTraveled;
	float velocityOut = VELCONTROL_P * distError;
	return velocityOut > abs(velocitySet) ? velocitySet : sgn(velocitySet)*velocityOut;
}

void setVelocities() {
	float velL, velR;
	switch (robotMode) {
		case MODE_NONE:
			velL = 0;
			velR = 0;
			break;
		case MODE_PATHLINE:
			velL = velocityControl(convertBytes2Float(robotState[0]), convertBytes2Float(robotState[1]));
			velR = velL;
			break;
		case MODE_PATHARC:
			float radius = convertBytes2Float(robotState[2]);
			float velMid = velocityControl(convertBytes2Float(robotState[0]), convertBytes2Float(robotState[1]));
			float omega = velMid / abs(radius);
			if (omega * (abs(radius) + WHEEL_DIST / 2) > WHEEL_VEL_LIMIT)
				omega = WHEEL_VEL_LIMIT / (abs(radius) + WHEEL_DIST / 2);
			velL = omega * (abs(radius) - sgn(radius)* WHEEL_DIST / 2);
			velR = omega * (abs(radius) + sgn(radius)* WHEEL_DIST / 2);
			break;
		case MODE_PATHVELOCITY:
			velL = convertBytes2Float(robotState[0]);
			velR = convertBytes2Float(robotState[1]);
			break;
	}
	analogWrite(pinWheelLeftSpeed, (int)constrain(abs(velL), 0, WHEEL_VEL_LIMIT));
	digitalWrite(pinWheelLeftDir, sgn(-velL));
	analogWrite(pinWheelRightSpeed, (int)constrain(abs(velR), 0, WHEEL_VEL_LIMIT));
	digitalWrite(pinWheelRightDir, sgn(-velR));
}