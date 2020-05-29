from swarm.templates import module
import socket
import json
from collections.abc import Mapping
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


class Requests(enum.Enum):
    READ = enum.auto()
    END = enum.auto()


class Requirements(module.Requirements):
    modulelist = ['gui']


class FSM(object):
    # pylint: disable=no-member
    _ok = True
    _request = None
    _request_new = False

    def __init__(self, pipe):
        self._pipe = pipe
        self._requirements = Requirements()
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

    def start(self):
        self._th_requests.start()
        self.to_INIT()
        while not self._request == Requests.END:
            self.change_state()
        self.to_END()

    def _thread_read_requests(self):
        while not self.is_END():
            if self._pipe.poll():
                recv = self._pipe.recv()
                if isinstance(recv, Mapping):
                    self._requirements.set_data(recv['name'], recv['data'])
                else:
                    self._request = self._pipe.recv()
                    self._request_new = True

    def request_READ(self):
        return self._request == Requests.READ

    def request_END(self):
        return self._request == Requests.END

    def on_enter_IDLE(self):
        self._pipe.send(self.state)

    def on_enter_INIT(self):
        while not self._requirements.have_data('gui'):
            pass
        data_gui = self._requirements.get_data('gui')
        self._ok &= self.serverclient.connect(**data_gui)
        self._ok &= int(self.serverclient.read(ServerReadMethods.CHECK))

    def on_enter_ERROR(self):
        self._pipe.send(self.state)

    def on_enter_END(self):
        self.serverclient.close()
        self._pipe.send(States.END)

    def on_enter_READ(self):
        self._request_new = False
        data = self.serverclient.read(ServerReadMethods.DATA)
        if data == False:
            self._ok &= False
        else:
            self._pipe.send(data)
