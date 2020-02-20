#include "headers/config.h"
#include "headers/message.h"
#include "headers/robot.h"
#include "headers/functions.h"

Robot robot = Robot(paramsDefault);
MessageBuffer buffer = MessageBuffer(MSG_BUFFERLEN);
Encoders encoders;

void setup() {
	pinMode(pinWheelLeftDir, OUTPUT);
	pinMode(pinWheelRightDir, OUTPUT);
	pinMode(pinWheelLeftSpeed, OUTPUT);
	pinMode(pinWheelRightSpeed, OUTPUT);

	pinMode(pinEncoderALeft, INPUT);
	pinMode(pinEncoderARight, INPUT);
	pinMode(pinEncoderBLeft, INPUT);
	pinMode(pinEncoderBRight, INPUT);

  Serial.begin(BAUDRATE);
  encoders = Encoders(pinEncoderALeft, pinEncoderBLeft, pinEncoderARight, pinEncoderBRight);
}

void loop() {
  switch (robot.getStatus()) {
    case STATUS_INIT:
    {
      robot.setStatus(STATUS_IDLE);
      break;
    }
    default:
    {
      readMessage();
      robot.setVelocity(pinWheelLeftSpeed, pinWheelLeftDir, pinWheelRightSpeed, pinWheelRightDir);
      robot.odometry(encoders);
    }
  }
}

void readMessage() {
  while (Serial.available() > 0) {
    buffer.append((uint8_t)Serial.read());
  }
  if (buffer.findCommand(MSG_HEADER)) {
    robot.update(buffer.getCommand());
  }
}