#define dir(x) ((x) < 0 ? HIGH : LOW)
#define sgn(x) ((x) < 0 ? -1 : 1)

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
#define MODE_PATHLINE 1
#define MODE_PATHARC 2
#define MODE_PATHTURN 3
#define MODE_PATHVELOCITY 4

#define STATUS_IDLE 0
#define STATUS_REC_OK 1
#define STATUS_REC_ERR 2

uint8_t robotMode = MODE_NONE;
uint8_t robotStatus = STATUS_IDLE;

#define ROBOTSTATE_LEN 3
#define ROBOTSENSOR_LER 1
#define PARAMETER_BYTE_LEN 4
float robotState[ROBOTSTATE_LEN] = {};
float robotSensor[ROBOTSENSOR_LER] =   {};
//
/*
SETTING: Message read
*/
#define BAUDRATE 9600
#define MSG_NONE 0
#define MSG_READ 1
#define MSG_END 2
#define MSG_ERROR 3
#define HEADER '*'

#define MSG_BUFFERLEN 20

const size_t idxRobotID = 0;
const size_t idxRobotMode = 1;
const size_t idxMsgLen = 2;
const size_t idxParamStart = 3;
const size_t msgModeLen = 3;

int readStatus = MSG_NONE;
size_t msgReadCount = 0;
uint8_t msgBuffer[MSG_BUFFERLEN] = {};
//
/*
SETTING: Odometry
*/
#define WHEEL_RADIUS 21
#define WHEEL_DIST 89
#define K 75*3

volatile long wheelCounterLeft = 0;
volatile long wheelCounterRight = 0;
unsigned long timeSaved = 0;
unsigned long timeDelta = 10;

float wheelLeftOmega = 0;
float wheelRightOmega = 0;
float wheelLeftDistance = 0;
float wheelRightDistance = 0;
float robotDistance = 0;
float robotOrient = 0;
//
/*
SETTING: Velocity control
*/
#define WHEEL_VEL_LIMIT 1.0f

const unsigned long timeIdle = 3000;
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
	Serial.begin(BAUDRATE);
}

void loop() {
	readCommand();
	changeRobotState();
	setVelocities();
	odometry();
}

void test() {
	/*digitalWrite(pinWheelLeftDir, LOW);
	digitalWrite(pinWheelRightDir, LOW);

	if (timeTraveled < 11000 && timeTraveled > 10000) {
		analogWrite(pinWheelLeftSpeed, 255);	
	}
	else {
		analogWrite(pinWheelLeftSpeed, 0);	
		Serial.println("time: " + (String)timeTraveled);
		Serial.println("dL: " + (String)wheelLeftDistance + " dR: " + (String)wheelRightDistance);
	}	*/
	robotState[0] = 0.5f;
	robotState[1] = PI;
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
		float drL = 2 * PI * (float)wheelCounterLeft * WHEEL_RADIUS / (K);
		float drR = 2 * PI * (float)wheelCounterRight * WHEEL_RADIUS / (K);
		wheelCounterRight = 0;
		wheelCounterLeft = 0;
		interrupts();
		//float dr = (drL + drR) / 2;
		//float dfi = (drR - drL) / WHEEL_DIST;
		wheelLeftDistance += drL;
		wheelRightDistance += drR;
		//robotOrient += dfi;
		//robotDistance += dr;
		
		//Serial.println("timeTraveled: " + (String)timeTraveled);
		//Serial.println("dL: " + (String)wheelLeftDistance + " dR: " + (String)wheelRightDistance);
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
	for (size_t idx = 0; idx < MSG_BUFFERLEN; idx++)
		msgBuffer[idx] = 0;
}

void readCommand() {
	while (Serial.available() > 0) {
		char readSymbol = Serial.read();
		switch (readStatus) {
			case MSG_NONE:
				if (readSymbol == HEADER)
					readStatus = MSG_READ;
				else
					robotStatus = STATUS_REC_ERR;
					sendStatus();
				break;
			case MSG_READ:
				if (msgReadCount < msgBuffer[idxMsgLen] + msgModeLen) {
					msgBuffer[msgReadCount] = (uint8_t)readSymbol;
					msgReadCount++;
				} else {
					if (checkMsg()) {
						readStatus = MSG_END;
						robotStatus = STATUS_REC_OK;
					}
					else {
						readStatus = MSG_ERROR;
						robotStatus = STATUS_REC_ERR;
						sendStatus();
					}
					
					msgReadCount = 0;
				}
			break;
		default:
			break;
		}
	}
}

void sendStatus() {
	Serial.println(robotStatus);
}

void resetRobotState() {
	robotMode = MODE_NONE;
	for (size_t idx = 0; idx < ROBOTSTATE_LEN; idx++) {
		robotState[idx] = 0;
	}
}

void changeRobotState() {
	if (readStatus == MSG_END) {
		sendStatus();
		robotMode = msgBuffer[idxRobotMode];
		for (size_t idx = 0; idx < msgBuffer[idxMsgLen] - 1; idx += PARAMETER_BYTE_LEN + 1) {
			uint8_t buffer[PARAMETER_BYTE_LEN] = {};
			for (size_t idxByte = 0; idxByte < PARAMETER_BYTE_LEN; idxByte++) {
				buffer[idxByte] = msgBuffer[idx + idxParamStart + idxByte + 1];
			}
			robotState[(size_t)msgBuffer[idx + idxParamStart]] = convertBytes2Float(buffer);
		}
		flushBuffer();
		readStatus = MSG_NONE;
		timeTraveled = 0;
		wheelLeftDistance = 0.0f;
		wheelRightDistance = 0.0f;
		robotDistance = 0.0f;
		robotOrient = 0.0f;
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
	}
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
}

void setVelocities() {
	float velL, velR;
	float dist, distL, distR;
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
			dist = robotState[1];
			errorCode += trajectory(dist, timeF, velL, distL);
			errorCode += trajectory(dist, timeF, velR, distR);
			break;
		}
		case MODE_PATHARC:
		{
			break;
		}
		case MODE_PATHTURN:
		{
			float angle = robotState[1];
			dist = angle*WHEEL_DIST/2;
			
			errorCode += trajectory(-dist, timeF, velL, distL);
			errorCode += trajectory(dist, timeF, velR, distR);
			break;
		}
		case MODE_PATHVELOCITY:
		{
			if (timeTraveled < timeIdle) {
				velL = constrain(robotState[0], -WHEEL_VEL_LIMIT, WHEEL_VEL_LIMIT);
				velR = constrain(robotState[1], -WHEEL_VEL_LIMIT, WHEEL_VEL_LIMIT);
			} else {
				errorCode = 1;
			}
			break;
		}
	}
	if (errorCode == 0) {
		digitalWrite(pinWheelLeftDir, dir(velL));
		digitalWrite(pinWheelRightDir, dir(velR));

		analogWrite(pinWheelRightSpeed, (int)abs(velR * 255));	
		analogWrite(pinWheelLeftSpeed, (int)abs(velL * 255));
	} else {
		robotMode = MODE_NONE;
	}
}