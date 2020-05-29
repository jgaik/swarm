import json
import numpy as np
import socket
import camera as cam
from threading import Thread

TCP_IP = '0.0.0.0'
TCP_PORT = 2020
HEADER_LEN = 10
BUFFER_LEN = 16

READ_RESPONSE = '0'
READ_MARKERS = '1'

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    camera = cam.Camera()
    with server, camera:
        server.bind((TCP_IP, TCP_PORT))
        server.listen(5)
        print(f"[Server]: Accepting clients")
        
        while True:
            client_socket, client_address = server.accept()
            print(f"[Server]: Client at {client_address} accepted")

            try:
                Thread(target=_clientThread, args=(client_socket, client_address, camera)).start()
            except:
                print(f"[Server]: !!!Could not start client {client_address} process!!!")

def _clientThread(client_socket, client_address, camera):
    while True:
        signal = client_socket.recv(1)
        signal = signal.decode('utf-8')

        if signal == READ_RESPONSE:
            msg = json.dumps(signal)

        elif signal == READ_MARKERS:
            msg = json.dumps(camera.getMarkerData())

        elif not signal:
            print(f"[Server]: The client at {client_address} has disconnected")
            client_socket.close()
            break

        else:
            continue

        msgBuffer = f"{len(msg):<{HEADER_LEN}}" + msg
            
        try:
            client_socket.send(msgBuffer.encode('utf-8'))
        except OSError:
            print(f"[Server]: The client at {client_address} has disconnected")
            client_socket.close()
            break
                
if __name__ == "__main__":
    main()