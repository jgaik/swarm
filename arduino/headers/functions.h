#ifndef FUNCTIONS_H
#define FUNCTIONS_H

class Encoders {
  public:
    Encoders();
    Encoders(uint8_t pinALeft, uint8_t pinBLeft, uint8_t pinARight, uint8_t pinBRight);
    void reset();
    volatile long counterLeft = 0;
    volatile long counterRight = 0;

  private:
    uint8_t _pinAL;
    uint8_t _pinBL;
    uint8_t _pinAR;
    uint8_t _pinBR;
    
    void encoderCountLeft();
    void encoderCountRight();
};

float convertBytes2Float(uint8_t floatBytes[4]);

int trajectory(float distanceFinal, size_t timeFinal, size_t timeTraveled, float &distanceTraveled, float &velocity);

#endif