import socket
import json

import enum
import transitions
import multiprocessing as mp
import threading as th

HEADER_LEN = 10
BUFFER_LEN = 16


class ServerReadMethods(enum.Enum):
    RESPONSE = '0'
    DATA = '1'
    CHECK = '2'


class Client:
    svTcpIP = '192.168.43.95'
    svTcpPort = 2020

    def __init__(self, tcp_ip=svTcpIP, tcp_port=svTcpPort):
        self.svTcpIP = tcp_ip
        self.svTcpPort = tcp_port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.server.connect((self.svTcpIP, self.svTcpPort))
            return True
        except:
            print("Camera server error")
            return False

    def close(self):
        self.server.close()

    def read(self, readMethod):
        msgLength = 0
        msgFull = ''
        newMsg = True
        self.server.sendall(readMethod.encode('utf-8'))
        while True:
            try:
                msg = self.server.recv(BUFFER_LEN)
                if newMsg:
                    msgLength = int(msg[:HEADER_LEN])
                    newMsg = False

                msgFull += msg.decode('utf-8')

                if len(msgFull) - HEADER_LEN >= msgLength:
                    msgFull = json.loads(msgFull[HEADER_LEN:])
                    break
            except:
                return False
        return msgFull


class States(enum.Enum):
    INIT = enum.auto()
    IDLE = enum.auto()
    READ = enum.auto()
    ERROR = enum.auto()
    END = enum.auto()


class Requests(enum.Enum):
    READ = enum.auto()
    END = enum.auto()


class FSM_Camera(object):
    # pylint: disable=no-member
    _ok = True
    _input = None
    _output = None
    _request = None
    _request_new = False

    def __init__(self):
        self.serverclient = Client()
        self._th_requests = th.Thread(target=self._thread_read_requests)
        self.machine = transitions.Machine(model=self,
                                           states=States,
                                           initial='none')

        self.machine.add_transition(trigger='change_state',
                                    source=States.INIT,
                                    dest=States.IDLE,
                                    conditions='_ok')

        self.machine.add_transition(trigger='change_state',
                                    source=States.INIT,
                                    dest=States.ERROR,
                                    unless='_ok')

        self.machine.add_transition(trigger='change_state',
                                    source=States.IDLE,
                                    dest=States.END,
                                    conditions=self.request_END,
                                    unless='_ok')

        self.machine.add_transition(trigger='change_state',
                                    source=States.IDLE,
                                    dest=States.READ,
                                    conditions=[
                                        self.request_READ, '_request_new'],
                                    unless='_ok')

        self.machine.add_transition(trigger='change_state',
                                    source=States.READ,
                                    dest=States.IDLE,
                                    conditions='_ok')

        self.machine.add_transition(trigger='change_state',
                                    source=States.READ,
                                    dest=States.ERROR,
                                    unless='_ok')

        self.machine.add_transition(trigger='change_state',
                                    source=States.ERROR,
                                    dest=States.END,
                                    conditions=self.request_END)

    def start(self, pipe_input, pipe_output):
        self._input = pipe_input
        self._output = pipe_output
        self.to_INIT()
        self._th_requests.start()
        while not self.is_END():
            self.change_state()

    def _thread_read_requests(self):
        while not self.is_END():
            if self._input.poll():
                self._request = self._input.recv()
                self._request_new = True

    def request_READ(self):
        return self._request == Requests.READ

    def request_END(self):
        return self._request == Requests.END

    def on_enter_IDLE(self):
        self._output.send(self.state)

    def on_enter_INIT(self):
        self._ok &= self.serverclient.connect()
        self._ok &= int(self.serverclient.read(ServerReadMethods.CHECK))

    def on_enter_ERROR(self):
        self._output.send(self.state)

    def on_enter_END(self):
        self.serverclient.close()
        self._output.send(States.END)

    def on_enter_READ(self):
        self._request_new = False
        data = self.serverclient.read(ServerReadMethods.DATA)
        if data == False:
            self._ok &= False
        else:
            self._output.send(data)
