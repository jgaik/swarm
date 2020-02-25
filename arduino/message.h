#ifndef MESSAGE_H
#define MESSAGE_H

#include "Arduino.h"
#include "config.h"
#include "functions.h"

struct command {
  uint8_t id;
  uint8_t mode;
  size_t parametersNumber;
  size_t* positions;
  float* values;
};

class CyclicBuffer {
  public:
    CyclicBuffer(size_t length);
    void push(uint8_t item);
    void get(size_t start, size_t length, uint8_t* out);
    uint8_t get(size_t idx);
    size_t length();
    void flush();
    void flush(size_t start, size_t len);
  private:
    uint8_t* _buffer;
    size_t _len;
    size_t _idx = 0;
};

class MessageBuffer {
  public:
    MessageBuffer(size_t length);
    void append(uint8_t reading);
    command getCommand();
    bool findCommand(uint8_t header);
  private:
    bool _updated = false;
    command _command;
    CyclicBuffer* _buffer;

    const size_t idxRobotID = 1;
    const size_t idxRobotMode = 2;
    const size_t idxMsgLen = 3;
    const size_t msgModeLen = 3;

    bool check(uint8_t* msg, size_t length);
    void extract(uint8_t* msg);
};

#endif