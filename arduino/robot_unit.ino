#define BAUDRATE 9600

const uint8_t pinEncoderALeft = 2;
const uint8_t pinEncoderBLeft = 5;
const uint8_t pinEncoderARight = 3;
const uint8_t pinEncoderBRight = 6;
const uint8_t pinWheelLeftDir = 7;
const uint8_t pinWheelRightDir = 8;
const uint8_t pinWheelLeftSpeed = 9;
const uint8_t pinWheelRightSpeed = 10;

volatile int counterLeft = 0;
volatile int counterRight = 0;
unsigned long timeSaved = 0;
int timeDelta = 50;

#define MSG_NONE 0
#define MSG_READ 1
#define MSG_END 2
#define MSG_ERROR 3
#define HEADER '*'
int msgStatus = MSG_NONE;
uint8_t msgBuffer[20] = {};
uint8_t robotMode;
uint8_t robotStatus;

#define ROBOTSTATE_LEN 3
#define ROBOTSENSOR_LER 1
#define PARAMETER_BYTE_LEN 4
uint8_t robotState[ROBOTSTATE_LEN][PARAMETER_BYTE_LEN] = {};
uint8_t robotSensor[ROBOTSENSOR_LER][PARAMETER_BYTE_LEN] ={};

void counterEncoderLeft() {
	int chA = digitalRead(pinEncoderALeft);
	int chB = digitalRead(pinEncoderBLeft);
	if ( (chA == HIGH && chB == HIGH) || (chA == LOW && chB == LOW) )
		counterLeft--;
	else
		counterLeft++;
}

void counterEncoderRight() {
	int chA = digitalRead(pinEncoderARight);
	int chB = digitalRead(pinEncoderBRight);
	if ( (chA == HIGH && chB == HIGH) || (chA == LOW && chB == LOW) )
		counterRight++;
	else
		counterRight--;
}

void calculateParams() {
	if (millis() - timeSaved >= timeDelta) {
		timeSaved = millis();
		noInterrupts();
		interrupts();
	}	
}

float convertBytes2Float(uint8_t floatBytes[4]) {
	uint32_t value32 = 0;
	for (size_t idx = 0; idx < 4; idx++) {
		value32 |= ((uint32_t)floatBytes[idx]) << (8 * idx);
	}
	return reinterpret_cast<float &>(value32);
}

bool checkMsg(uint8_t msg[20], size_t msgLen) {
	int modulo = 256;
	uint8_t sum = 0;
	for (size_t idx = 0; idx < msgLen - 1; idx++) {
		sum += msg[idx];
	}
	sum = modulo - sum%modulo - 1;
	return sum == msg[msgLen - 1];
}

bool readCommand() {
	char header = '*';
	size_t idxRobotID = 0;
	size_t idxRobotMode = 1;
	size_t idxMsgLen = 2;
	size_t idxParamStart = 4;

	size_t commandLen = 3;
	size_t msgLen = 0;

	bool commandRead = false;
	bool msgRead = false;
	bool newCommand = false;

	uint8_t msgBuffer[20];
	size_t readCount = 0;
	if (Serial.available() > 0) {
		Serial.print("[Arduino Robot]: ");
		Serial.println(Serial.available());
	}
	while (Serial.available() > 0) {
		char readSymbol = Serial.read();
		Serial.println(readSymbol);
		if ( (commandRead && readCount < commandLen) || (msgRead && readCount < msgLen) ) {
			msgBuffer[readCount] = uint8_t(readSymbol);
			readCount++;
		} else if (commandRead && readCount >= commandLen) {
			commandRead = false;
			msgRead = true;
			msgLen = msgBuffer[idxMsgLen] + commandLen;
			Serial.print("[Arduino Robot]: Msg length = ");
			Serial.println(msgBuffer[idxMsgLen], DEC);
		} else if (msgRead && readCount >= msgLen) {
			Serial.print("[Arduino Robot]: Check sum = ");
			Serial.println(msgBuffer[msgLen - 1], HEX);
			break;
		}

		if (!newCommand && readSymbol == header) {
			Serial.println("[Arduino Robot]: New msg received");
			newCommand = true;
			commandRead = true;
		}
	}
	if (newCommand){
		Serial.print("[Arduino Robot]: Read character count = ");
		Serial.println(readCount, DEC);
	}
	if (newCommand && checkMsg(msgBuffer, msgLen)) {
		Serial.println("[Arduino Robot]: New msg is OK");
		robotMode = msgBuffer[idxRobotMode];
		for (size_t idx = idxParamStart; idx < msgLen - 1; idx += PARAMETER_BYTE_LEN + 1) {
			for (size_t idxByte = 0; idxByte < PARAMETER_BYTE_LEN; idxByte++) {
				robotState[(size_t)msgBuffer[idx]][idxByte] = msgBuffer[idx + idxByte + 1];
			}
		}
	}
	return newCommand;
}

void setup() {
	pinMode(pinWheelLeftDir, OUTPUT);
	pinMode(pinWheelRightDir, OUTPUT);
	pinMode(pinWheelLeftSpeed, OUTPUT);
	pinMode(pinWheelRightSpeed, OUTPUT);

	attachInterrupt(digitalPinToInterrupt(pinEncoderALeft), counterEncoderLeft, CHANGE);
	attachInterrupt(digitalPinToInterrupt(pinEncoderARight), counterEncoderRight, CHANGE);
	Serial.begin(BAUDRATE);
}

void loop() {
	if (readCommand()) {
		Serial.println("[Arduino Robot]: Robot state:");
		for (size_t idx = 0; idx < ROBOTSTATE_LEN; idx++) {
			Serial.println(idx);
			for (size_t i = 0; i < PARAMETER_BYTE_LEN; i++) {
				Serial.print(robotState[idx][i], DEC);
			}
			Serial.println("");
			Serial.println(convertBytes2Float(robotState[idx]), 2);
		}
	}
}