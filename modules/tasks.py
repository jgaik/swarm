"""
import tasklist
import importlib

class Task:
    'class for managing and storing task parameters'
    
    def __init__(self, taskname):
        self.name = taskname

    def run(self, cameraInput, userInput):
        return importlib.import_module(f"tasklist.{self.name}").run(cameraInput, userInput)
"""
from swarm.shared import config
from swarm.shared.templates import modules
import enum
import transitions


class States(enum.Enum):
    INIT = enum.auto()
    IDLE = enum.auto()
    ERROR = enum.auto()
    END = enum.auto()


class Requirements(modules.BaseRequirements):
    datatags = ['task']


class FSM(modules.BaseFSM):
    #pylint: disable=no-member
    _ok = True

    def __init__(self, pipe):
        super(FSM, self).__init__(pipe, config.Request(), Requirements())

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
                'conditions': self._ok
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.ERROR,
                'unless': self._ok
            },
            {
                'trigger': 'change_state',
                'source': States.IDLE,
                'dest': States.END,
                'conditions': self._request.is_END
            },
            {
                'trigger': 'change_state',
                'source': States.ERROR,
                'dest': States.END,
                'conditions': self._request.is_END
            }
        ]

        self.machine = transitions.Machine(model=self,
                                           states=States,
                                           initial='none',
                                           transitions=list_transitions)

    def on_enter_INIT(self):
        self.send_response(config.Response.INIT, data={'tasks': []})

    def on_enter_IDLE(self):
        self.send_response(config.Response.READY)

    def on_enter_ERROR(self):
        self.send_response(config.Response.ERROR)

    def on_enter_END(self):
        self.send_response(config.Response.END)
