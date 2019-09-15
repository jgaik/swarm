import socket
import json
import time

TCP_IP = '192.168.0.12'
TCP_PORT = 5050
HEADER_LEN = 10
BUFFER_LEN = 16

READ_RESPONSE = '0'
READ_MARKERS = '1'

class Client:
  counter = []

  def __init__(self):
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  def __enter__(self):
    self.server.connect((TCP_IP, TCP_PORT))

  def __exit__(self, _, __, ___):
    self.server.close()

  def read(self, readMethod):
    msgLength = 0
    msgFull = ''
    newMsg = True
    t = time.time()
    self.server.sendall(readMethod.encode('utf-8'))
    while True:
      msg = self.server.recv(BUFFER_LEN)
      if newMsg:
        msgLength = int(msg[:HEADER_LEN])
        newMsg = False
        
      msgFull += msg.decode('utf-8')

      if len(msgFull) - HEADER_LEN >= msgLength:
        self.counter.append((time.time() - t)*1000)
        msgFull = json.loads(msgFull[HEADER_LEN:])
        break
        
    return msgFull