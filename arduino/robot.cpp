#include "robot.h"

Robot::Robot(const float* paramsDefault) {
  _parametersDefault = paramsDefault;
  reset();
  _pid = ControllerPID(_parameters[3], _parameters[4], _parameters[5]);
}

Robot::~Robot() {
  //delete [] _parameters;
  //delete [] _settings;
  //delete [] _sensors;
}

void Robot::reset() {
  for (size_t idx = 0; idx < ROBOTSETTINGS_LEN; idx++) {
    _settings[idx] = 0.0f;
  }
  for (size_t idx = 0; idx < ROBOTSENSORS_LEN; idx++) {
    _sensors[idx] = 0.0f;
  }
  for (size_t idx = 0; idx < ROBOTPARAMS_LEN; idx++) {
    _parameters[idx] = _parametersDefault[idx];
  }
}

void Robot::reset(const float* paramsDefault) {
  _parametersDefault = paramsDefault;
  reset();
}

uint8_t Robot::getID() {
  return _id;
}

uint8_t Robot::getMode() {
  return _mode;
}

void Robot::setMode(uint8_t modeCode) {
  _mode = modeCode;
}

uint8_t Robot::getStatus() {
  return _status;
}

void Robot::setStatus(uint8_t statusCode) {
  _status = statusCode;
}

bool Robot::update(Command cmd) {
  switch (cmd.mode) {
		case MODE_INIT: 
		{
			_id = cmd.id;
      for (size_t idx = 0; idx < cmd.parametersNumber; idx++) {
        _parameters[cmd.positions[idx]] = cmd.values[idx];
      }
			return true;
		}

		default: 
		{
			if (_id == cmd.id) {
				_mode = cmd.mode;
        for (size_t idx = 0; idx < cmd.parametersNumber; idx++) {
          _settings[cmd.positions[idx]] = cmd.values[idx];
        }
				_timeTraveled = 0;
				_distL = 0.0f;
				_distR = 0.0f;
        _pid.reset(); 
				return true;

			} else {
				return false;
			}
		}
	}
}

void Robot::odometry(Encoders& encoders) {
  size_t timeDiff = millis() - _timeSaved;
  if (timeDiff >= _timeDelta) {
    _timeSaved = millis();
    _timeTraveled += timeDiff;
    noInterrupts();
    _distL += 2 * PI * (float) encoders.counterLeft * _parameters[1] / (K);
    _distR += 2 * PI * (float) encoders.counterRight * _parameters[2] / (K);
    encoders.reset();
    interrupts();
  }
}

void Robot::setVelocity(uint8_t pinL, uint8_t pinLDir, uint8_t pinR, uint8_t pinRDir) {
  size_t timeF = _settings[0];
  float distFinL, distFinR, distL, distR;
  int errorCode = 0;

	switch (_mode) {
		case MODE_NONE:
		{	
			_velL = 0.0f;
			_velR = 0.0f;
			break;
		}

		case MODE_PATHLINE:
		{
			distFinL = _settings[1];
			distFinR = distFinL;
			errorCode |= trajectory(distFinL, timeF, _timeTraveled, distL, _velL);
			errorCode |= trajectory(distFinR, timeF, _timeTraveled, distR, _velR);
			_pid.update(distL-_distL, distR-_distR,_velL,_velR);
      break;
		}
		case MODE_PATHARC:
		{
			distFinL = (_settings[2]-_parameters[0]/2)*_settings[1];
			distFinR = (_settings[2]+_parameters[0]/2)*_settings[1];
			errorCode |= trajectory(distFinL, timeF, _timeTraveled, distL, _velL);
			errorCode |= trajectory(distFinR, timeF, _timeTraveled, distR, _velR);
			_pid.update(distL-_distL, distR-_distR,_velL,_velR);
      break;
		}
		case MODE_PATHTURN:
		{
			distFinL = -_settings[1] * _parameters[0]/2;
			distFinR = -distFinL;
			errorCode |= trajectory(distFinL, timeF, _timeTraveled, distL, _velL);
			errorCode |= trajectory(distFinR, timeF, _timeTraveled, distR, _velR);
			_pid.update(distL-_distL, distR-_distR,_velL,_velR);
			break;
		}
		case MODE_PATHVELOCITY:
		{
			if (_timeTraveled < timeF) {
				_velL = constrain(_settings[1], -VEL_LIMIT, VEL_LIMIT);
				_velR = constrain(_settings[2], -VEL_LIMIT, VEL_LIMIT);
			} else {
				errorCode |= 1;
			}
			break;
		}
	}
	if (errorCode == 0) {
		digitalWrite(pinLDir, DIR(_velL));
		digitalWrite(pinRDir, DIR(_velR));

		analogWrite(pinR, (int)abs(_velR * 255));	
		analogWrite(pinL, (int)abs(_velL * 255));
		
	} else {
		_mode = MODE_NONE;
	}
}

ControllerPID::ControllerPID() {
  reset();
}

ControllerPID::ControllerPID(float Kp, float Ki, float Kd) {
  _kp = Kp;
  _ki = Ki;
  _kd = Kd;
  reset();
}

void ControllerPID::update(float errL, float errR, float& velL, float& velR) {
  _errLPrev = _errL;
  _errRPrev = _errR;
  _errL = errL;
  _errR = errR;
  float sumL = _errLSum + _errL;
  float sumR = _errRSum + _errR;

  float velocityL = velL + _errL*_kp + sumL*_ki + _errLPrev*_kd;
  float velocityR = velR + _errR*_kp + sumR*_ki + _errRPrev*_kd;

  if (abs(velocityL) > VEL_LIMIT) {
    velL += _errL*_kp + _errLSum*_ki + _errLPrev*_kd;
  } else {
    velL = velocityL;
    _errLSum = sumL;
  }

  if (abs(velocityR) > VEL_LIMIT) {
    velR += _errR*_kp + _errRSum*_ki + _errRPrev*_kd;
  } else {
    velR = velocityR;
    _errRSum = sumR;
  }
}

void ControllerPID::reset() {
  _errL = 0.0f;
  _errR = 0.0f;
  _errLSum = 0.0f;
  _errRSum = 0.0f;
  _errLPrev = 0.0f;
  _errRPrev = 0.0f;
}