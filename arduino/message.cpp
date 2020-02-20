#include "message.h"

CyclicBuffer::CyclicBuffer(size_t length) {
  _buffer = new uint8_t[length]();
  _len = length;
}

void CyclicBuffer::push(uint8_t item) {
  _buffer[_idx] = item;
  _idx = (_idx + 1) % _len;
}

uint8_t* CyclicBuffer::get(size_t start, size_t len) {
  uint8_t* out = new uint8_t[len];
  for (size_t idx = 0; idx < len; idx ++) {
    out[idx] = _buffer[(idx + start) % _len];
  }
  return out;
}

uint8_t CyclicBuffer::get(size_t idx) {
  return _buffer[idx % _len];
}

void CyclicBuffer::flush() {
  _buffer = new uint8_t[_len]();
}

void CyclicBuffer::flush(size_t start, size_t len) {
  for (size_t idx = 0; idx < len; idx++) {
    _buffer[(idx + start) % _len] = 0;
  }
}

size_t CyclicBuffer::length() {
  return _len;
}

MessageBuffer::MessageBuffer(size_t length) {
  _buffer = new CyclicBuffer(length);
}

void MessageBuffer::append(uint8_t reading) {
  _buffer->push(reading);
  _updated = true;
}

bool MessageBuffer::findCommand(uint8_t header) {
  if (_updated) {
    for (size_t idxHeader = 0; idxHeader < _buffer->length(); idxHeader++) {
      if (_buffer->get(idxHeader) == header) {
        size_t len = _buffer->get(idxHeader + idxMsgLen) + msgModeLen + 1;
        uint8_t* tempMsg = _buffer->get(idxHeader, len);
        if (check(tempMsg, len)) {
          Serial.println("TU JESTEM");
          extract(tempMsg);
          _buffer->flush(idxHeader, len);
          return true;
        }
      }
    }
    _updated = false;
  }
  return false;
}

command MessageBuffer::getCommand() {
  return _command;
}

bool MessageBuffer::check(uint8_t* msg, size_t length) {
  uint8_t modulo = 255;
	uint8_t sum = 0;
	for (size_t idx = 1; idx < length - 1; idx++) {
		sum += msg[idx];
	}
	sum = modulo - sum;
	return sum == msg[length - 1];
}

void MessageBuffer::extract(uint8_t* msg) {
  _command.id = msg[idxRobotID];
  _command.mode = msg[idxRobotMode];
  _command.parametersNumber = (msg[idxMsgLen] - 1) / (PARAMETER_BYTE_LEN + 1);
  _command.positions = new size_t[_command.parametersNumber];
  _command.values = new float[_command.parametersNumber];
  for (size_t idx = 0; idx < _command.parametersNumber; idx ++) {
    uint8_t paramBuffer[PARAMETER_BYTE_LEN];
    for (size_t idxByte = 0; idxByte < PARAMETER_BYTE_LEN; idxByte++) {
      paramBuffer[idxByte] = msg[idxMsgLen + 1 + idx*(PARAMETER_BYTE_LEN + 1) + idxByte + 1];
    }
    _command.positions[idx] = msg[idx];
    _command.values[idx] = convertBytes2Float(paramBuffer);
  }
}