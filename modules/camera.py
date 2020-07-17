from swarm.templates import module
import socket
import json
import enum
import transitions
import multiprocessing as mp
import threading as th
import sys

HEADER_LEN = 10
BUFFER_LEN = 16


class ServerReadMethods(enum.Enum):
    RESPONSE = '0'
    DATA = '1'
    CHECK = '2'


class Client:

    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, tcp_ip, tcp_port):
        try:
            self.server.connect((tcp_ip, tcp_port))
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


class Requests(module.BaseRequests):
    READ = enum.auto()
    END = enum.auto()


class Requirements(module.BaseRequirements):
    modulelist = ['gui']


class FSM(module.BaseFSM):
    # pylint: disable=no-member
    _ok = True

    def __init__(self, pipe):
        super(FSM, self).__init__(pipe, Requests(), Requirements())
        self.serverclient = Client()

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
                                    conditions=self._request.is_END,
                                    unless='_ok')

        self.machine.add_transition(trigger='change_state',
                                    source=States.IDLE,
                                    dest=States.READ,
                                    conditions=self._request.is_READ,
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

    def on_enter_IDLE(self):
        self.send_data()

    def on_enter_INIT(self):
        self.send_data(name=__name__)
        self._requirements.wait_gui()
        data_gui = self._requirements.get_data('gui')
        self._ok &= self.serverclient.connect(**data_gui)
        self._ok &= int(self.serverclient.read(ServerReadMethods.CHECK))

    def on_enter_ERROR(self):
        self._pipe.send(self.state)

    def on_enter_END(self):
        self.serverclient.close()
        self.send_data()

    def on_enter_READ(self):
        self._request_new = False
        data = self.serverclient.read(ServerReadMethods.DATA)
        if data == False:
            self._ok &= False
        else:
            self.send_data(data={'tasks': data})
