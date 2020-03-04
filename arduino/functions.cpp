#include "functions.h"

float convertBytes2Float(uint8_t floatBytes[4]) {
	uint32_t value32 = 0;
	for (size_t idx = 0; idx < 4; idx++) {
		value32 |= ((uint32_t)floatBytes[3 - idx]) << (8 * idx);
	}
	return reinterpret_cast<float &>(value32);
}

int trajectory(float distanceFinal, size_t timeFinal, size_t timeTraveled, float &distanceTraveled, float &velocity) {
	float velConst = 0.5f;
	float blend = 0.15f;
	float t = (float)timeTraveled / timeFinal;
	float velMax = distanceFinal / timeFinal / (1 - blend) / velConst;
	if (velMax > 1.0f)
		return TRAJECTORY_ERR;

	if (t < blend) {
		distanceTraveled = distanceFinal * ( t * t / 2 / blend ) / (1 - blend);
		velocity = velMax * ( t / blend );
		return 0;
	}
	if (t < 1.0f - blend) {
		distanceTraveled = distanceFinal * ( t - blend/2 ) / (1 - blend);
		velocity = velMax;
		return 0;
	} else 
	if (t < 1.0f) {
		distanceTraveled = distanceFinal * ( t - blend/2 - (t - 1 + blend)*(t - 1 + blend)/2/blend ) / (1 - blend);
		velocity = velMax * ( (1 - t) / blend );
		return 0;
	} else {
		distanceTraveled = distanceFinal * 1.0;
		velocity = 0.0f;
		return TRAJECTORY_END;
	}
}

Encoders::Encoders(uint8_t pinALeft, uint8_t pinBLeft, uint8_t pinARight, uint8_t pinBRight) {
  _pinAL = pinALeft;
  _pinBL = pinBLeft;
  _pinAR = pinARight;
  _pinBR = pinBRight;
}

void Encoders::reset() {
  counterRight = 0;
  counterLeft = 0;
}

void Encoders::countLeft() {
  if(digitalRead(_pinBL) == LOW)
    counterLeft--;
  else 
    counterLeft++;
}

void Encoders::countRight() {
  if(digitalRead(_pinBR) == LOW)
    counterRight++;
  else
    counterRight--;
}