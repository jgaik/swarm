import socket
import json

HEADER_LEN = 10
BUFFER_LEN = 16

READ_RESPONSE = '0'
READ_MARKERS = '1'

class Client:
  svTcpIP = '192.168.43.95'
  svTcpPort = 2020

  def __init__(self, tcp_ip = svTcpIP, tcp_port = svTcpPort):
    self.svTcpIP = tcp_ip
    self.svTcpPort = tcp_port
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  def __enter__(self):
    self.server.connect((self.svTcpPort, self.svTcpPort))
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