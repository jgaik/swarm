#include "config.h"
#include "functions.h"
#include "message.h"
#include "robot.h"

Robot robot(paramsDefault);
MessageBuffer buffer(MSG_BUFFERLEN);
Encoders encoders(pinEncoderALeft, pinEncoderBLeft, pinEncoderARight, pinEncoderBRight);

void setup() {
	pinMode(pinWheelLeftDir, OUTPUT);
	pinMode(pinWheelRightDir, OUTPUT);
	pinMode(pinWheelLeftSpeed, OUTPUT);
	pinMode(pinWheelRightSpeed, OUTPUT);

	pinMode(pinEncoderALeft, INPUT);
	pinMode(pinEncoderARight, INPUT);
	pinMode(pinEncoderBLeft, INPUT);
	pinMode(pinEncoderBRight, INPUT);

  attachInterrupt(pinEncoderALeft, interruptLeft, RISING);
  attachInterrupt(pinEncoderARight, interruptRight, RISING);
  Serial.begin(BAUDRATE);
}

void loop() {
  switch (robot.getStatus()) {
    case STATUS_INIT:
    {
      messageRead(MSG_HEADER);
      break;
    }
    case STATUS_IDLE:
    {
      messageRead(MSG_HEADER);
      break;
    }
    case STATUS_WORKING:
    {
      robot.setVelocity(pinWheelLeftSpeed, pinWheelLeftDir, pinWheelRightSpeed, pinWheelRightDir);
      robot.odometry(encoders);
      break;
    }
    case STATUS_ERROR:
    {
      messageRead(MSG_HEADER);
      break;
    }
  }
}

void interruptLeft() {
  encoders.countLeft();
}

void interruptRight() {
  encoders.countRight();
}

void messageRead(uint8_t header) {
  while (Serial.available() > 0) {
    buffer.append((uint8_t)Serial.read());
  }
  if (buffer.findCommand(header)) {
    robot.update(buffer.getCommand());
  }
}
