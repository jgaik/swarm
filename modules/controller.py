import threading as th
from collections.abc import Mapping
import enum
import transitions
from swarm.shared import config
from swarm.shared.templates.data import LockedData


class ModuleData:

    def __init__(self):
        self._lock = th.Lock()
        self._data = {}
        self._names = []

    def set(self, name, data):
        new = False
        with self._lock:
            if not name in self._names:
                new = True
                self._names.append(name)
        if new:
            self._data[name] = LockedData(False, data)
        else:
            self._data[name].set(data)


class Module:

    def __init__(self, pipe):
        self.name = ""
        self.requirements = []
        self.data = ModuleData()

        self._pipe = pipe
        self._response = config.Response()
        self._request = None
        self._th_responses = th.Thread(target=self._thread_read_response)
        self._senttags = []
        self._active = False
        self._lock = th.Lock()

    def _thread_read_response(self):
        while self._active:
            if self._pipe.poll():
                recv = self._pipe.recv()
                if isinstance(recv, Mapping):
                    if recv['response'] == config.Response.INIT:
                        self.name = recv['name']
                        self.requirements = recv['requirements']
                    self._response.set_current(recv['response'])
                    for (name, data) in recv['data']:
                        self.data.set(name, data)
                else:
                    self._response.set_current(recv)

    def activate(self):
        self._active = True
        self._th_responses.start()

    def deactivate(self):
        self._active = False

    def send_request(self, request, data=None):
        self._request = request
        if data is None:
            self._pipe.send(request)
        else:
            self._pipe.send({
                'request': request,
                'data': data
            })
            with self._lock:
                self._senttags.append(data.keys())

    def update(self, updated_tag):
        with self._lock:
            try:
                self._senttags.remove(updated_tag)
            except:
                pass

    def is_response(self, response):
        return getattr(self._response, "is_" + response.name)()


class States(enum.Enum):
    INIT = enum.auto()
    IDLE = enum.auto()
    END = enum.auto()
    ERROR = enum.auto()


class FSM:
    # pylint: disable=no-member

    def __init__(self, *pipes):
        self._online = False
        self.modules = []
        for pipe in pipes:
            self.modules.append(Module(pipe))

        list_transitions = [
            {
                'trigger': 'change_state',
                'source': 'none',
                'dest': States.INIT,
                'conditions': True
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.IDLE,
                'conditions': self.modules_ready,
                'unless': self.module_error
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.ERROR,
                'conditions': self.module_error
            },
        ]

        self.machine = transitions.Machine(model=self,
                                           states=States,
                                           initial='none',
                                           transitions=list_transitions)

    def start(self):
        self._online = True
        for m in self.modules:
            m.activate()
        while self._online:
            self.change_state()

    def on_enter_INIT(self):
        for m in self.modules:
            m.send_request(config.Request.INIT)

    def modules_INIT_thread(self, module: Module):
        while not module.is_response(config.Response.READY):
            pass

    def modules_response(self, response):
        return all([m.is_response(response) for m in self.modules])

    def modules_ready(self):
        return self.modules_response(config.Response.READY)

    def modules_end(self):
        return self.modules_response(config.Response.END)

    def module_response(self, response):
        return any([m.is_response(response) for m in self.modules])

    def module_error(self):
        return self.module_response(config.Response.ERROR)
