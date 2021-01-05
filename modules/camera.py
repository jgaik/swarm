from swarm.shared import config
from swarm.shared.templates import modules
import socket
import json
import enum
import transitions
import multiprocessing as mp
import threading as th
import sys

HEADER_LEN = 10
BUFFER_LEN = 16


class ServerRequest(enum.Enum):
    RESPONSE = '0'
    DATA = '1'
    CHECK = '2'


class ServerResponse(enum.Enum):
    OK = '1'
    ERROR = '0'


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


class Requirements(modules.BaseRequirements):
    datatags = ['setup_camera']


class FSM(modules.BaseFSM):
    # pylint: disable=no-member
    _ok = True

    def __init__(self, pipe):
        super(FSM, self).__init__(pipe, config.Request(), Requirements())
        self.serverclient = Client()

        list_transitions = [
            {
                'trigger': 'change_state',
                'source': 'none',
                'dest': States.INIT,
                'conditions': self._request.is_INIT
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.IDLE,
                'conditions': self._ok,
                'unless': self._request.is_END
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.END,
                'conditions': self._request.is_END
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.ERROR,
                'conditions': True,
                'unless': self._ok
            },
            {
                'trigger': 'change_state',
                'source': States.IDLE,
                'dest': States.ERROR,
                'conditions': True,
                'unless': self._ok
            },
            {
                'trigger': 'change_state',
                'source': States.ERROR,
                'dest': States.END,
                'conditions': self._request.is_END,
                'unless': False
            },
            {
                'trigger': 'change_state',
                'source': States.IDLE,
                'dest': States.END,
                'conditions': self._request.is_END,
                'unless': False
            },
            {
                'trigger': 'change_state',
                'source': States.IDLE,
                'dest': States.READ,
                'conditions': self._request.is_READ,
                'unless': False
            },
            {
                'trigger': 'change_state',
                'source': States.READ,
                'dest': States.IDLE,
                'conditions': self._ok,
                'unless': False
            },
            {
                'trigger': 'change_state',
                'source': States.READ,
                'dest': States.ERROR,
                'conditions': True,
                'unless': self._ok
            }
        ]

        self.machine = transitions.Machine(model=self,
                                           states=States,
                                           transitions=list_transitions,
                                           initial='none')

    def on_enter_IDLE(self):
        self.send_response(config.Response.READY)

    def on_enter_INIT(self):
        self.send_response(config.Response.INIT)
        self._request.wait_new()
        if self._requirements.have_data('setup_camera'):
            data = self._requirements.get_data('setup_camera')
            if not self.serverclient.connect(**data):
                self._ok = False
                return
            if self.serverclient.read(ServerRequest.CHECK) == ServerResponse.ERROR:
                self._ok = False
                return

    def on_enter_ERROR(self):
        self.send_response(config.Response.ERROR)

    def on_enter_END(self):
        self.serverclient.close()
        self.send_response(config.Response.OK)

    def on_enter_READ(self):
        data = self.serverclient.read(ServerRequest.DATA)
        if data == False:
            self._ok &= False
            self.send_response(config.Response.ERROR)
        else:
            self.send_response(config.Response.OK, {'tasks': data})
