#ifndef ROBOT_H
#define ROBOT_H

#include "config.h"
#include "functions.h"
#include "message.h"

class Robot {
  public:
    Robot(const float paramsDefault[]);
    
    uint8_t getMode();
    void setMode(uint8_t modeCode);
    uint8_t getID();
    uint8_t getStatus();
    void setStatus(uint8_t statusCode);
    bool update(Command cmd);
    void odometry(Encoders encoders);

    void reset();
    void reset(const float* paramsDefault);
    ~Robot();
  private:
    float _parameters[ROBOTPARAMS_LEN];
    float _settings[ROBOTSETTINGS_LEN];
    float _sensors[ROBOTSENSORS_LEN];

    const float* _parametersDefault;

    uint8_t _id = 0;
    uint8_t _mode = MODE_NONE;
    uint8_t _status = STATUS_INIT;

    float _velL = 0.0f;
    float _velR = 0.0f;

    float _distL = 0.0f;
    float _distR = 0.0f;
     
     ControllerPID pid;
};

class ControllerPID {
  public:
    ControllerPID();
    ControllerPID(float Kp, float Ki = 0.0f, float Kd = 0.0f);

    void update(float errL, float errR);
    void reset();
  
  private:
    float _kp = 0.0f;
    float _ki = 0.0f;
    float _kd = 0.0f;

    float _errL;
    float _errR;
    float _errLSum;
    float _errRSum;
    float _errLPrev;
    float _errRPrev;

};


#endif 