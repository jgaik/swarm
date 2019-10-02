#define BAUDRATE 9600
#define STATE_PARAMS_LEN 4

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

uint8_t robotState[STATE_PARAMS_LEN + 1][4] = {};
uint8_t robotCommand[16] = {};

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

bool checkMsg(char msg) {
	
}

void readCommand() {
	char header = char(255);
	size_t commandLen = 3;
	size_t msgLen = 0;

	bool commandRead = false;
	bool msgRead = false;
	bool newCommand = false;

	char msgBuffer[16];
	uint8_t commandBuffer[3];

	size_t readCount = 0;
	while (Serial.available() > 0) {
		char readSymbol = Serial.read();

		if (!newCommand && readSymbol == header) {
			newCommand = true;
			commandRead = true;
		}

		if (commandRead && readCount < commandLen) {
			commandBuffer[readCount] = uint8_t(readSymbol);
			readCount++;
		} else if (commandRead && readCount >= commandLen) {
			commandRead = false;
			msgRead = true;
			msgLen = commandBuffer[commandLen - 1];
			readCount = 0;
		}

		if (msgRead && readCount < msgLen) {
			msgBuffer[readCount] = readSymbol;
			readCount++;
		} else if (msgRead && readCount >= msgLen) {
			break;
		}
	}

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
}