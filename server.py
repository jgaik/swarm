import socket
import json

TCP_IP = '192.168.43.95'
TCP_PORT = 2020
HEADER_LEN = 10
BUFFER_LEN = 16

READ_RESPONSE = '0'
READ_MARKERS = '1'

class Client:

  def __init__(self):
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  def __enter__(self):
    self.server.connect((TCP_IP, TCP_PORT))
    return self

  def __exit__(self, _, __, ___):
    self.server.close()

  def read(self, readMethod):
    msgLength = 0
    msgFull = ''
    newMsg = True
    self.server.sendall(readMethod.encode('utf-8'))
    while True:
      msg = self.server.recv(BUFFER_LEN)
      if newMsg:
        msgLength = int(msg[:HEADER_LEN])
        newMsg = False
        
      msgFull += msg.decode('utf-8')

      if len(msgFull) - HEADER_LEN >= msgLength:
        msgFull = json.loads(msgFull[HEADER_LEN:])
        break
        
    return msgFull