import threading as th
import enum
from collections.abc import Mapping


class BaseRequirements:
    modulelist = []

    def __init__(self):
        self._data = {}
        self._events = {}
        self._lock = th.Lock()
        for ml in self.modulelist:
            self._data[ml] = None
            self._events[ml] = th.Event()
            self._add_method_have(ml)

    def have_data(self, require_name=None):
        if require_name is None:
            return all([x.is_set() for x in self._events.values()])
        if isinstance(require_name, list):
            return all([self._events[name].is_set() for name in require_name if name in self.modulelist])
        else:
            if require_name in self.modulelist:
                self._events[require_name].is_set()
            else:
                return False

    def wait_data(self, require_name=None):
        if require_name is None:
            for e in self._events.values():
                e.wati()
        if isinstance(require_name, list):
            for name in require_name:
                if name in self.modulelist:
                    self._events[name].wait()
        else:
            if require_name in self.modulelist:
                self._events[require_name].wait()
            else:
                print(
                    f"[FSM]: !!!Incorrect module name requested - {require_name}!!!")

    def get_data(self, require_name=None):
        if require_name is None:
            with self._lock:
                return self._data
        tmp = {}
        if isinstance(require_name, list):
            for name in require_name:
                if name in self.modulelist:
                    with self._lock:
                        tmp[name] = self._data[name]
                        self._data[name] = None
                        self._events[name].clear()
        else:
            if require_name in self.modulelist:
                with self._lock:
                    tmp = self._data[require_name]
                    self._data[require_name] = None
                    self._events[require_name].clear()
        return tmp

    def set_data(self, require_name, require_data):
        if require_name in self.modulelist:
            with self._lock:
                self._data[require_name] = require_data
            self._events[require_name].set()

    def _add_method_have(self, name):
        def fn(self=self):
            return self.have_data(name)
        setattr(self, 'have_' + name, fn)

    def _add_method_wait(self, name):
        def fn(self=self):
            self._events[name].wait()
        setattr(self, 'wait_' + name, fn)


class BaseRequests:

    def __init__(self):
        self._events = {}
        self._event_new = th.Event()
        attr = dir(self)
        for name in attr[0:attr.index("__class__")]:
            self._events[name] = th.Event()
            self._add_method_is(name)
            self._add_method_wait(name)

    def set_current(self, request):
        self._event_new.set()
        for key in self._events:
            if key == request:
                self._events[key].set()
            else:
                self._events[key].clear()

    def is_request(self, request):
        return self._events[request].is_set()

    def is_new(self):
        return self._event_new.is_set()

    def wait_new(self):
        self._event_new.wait()
        self._event_new.clear()

    def _add_method_is(self, name):
        def fn(self=self):
            return self.is_request(name)
        setattr(self, 'is_' + name, fn)

    def _add_method_wait(self, name):
        def fn(self=self):
            self._events[name].wait()
        setattr(self, 'wait_' + name, fn)


class BaseFSM(object):
    # pylint: disable=no-member
    def __init__(self, pipe, requests, requirments):
        self._online = False
        self._pipe = pipe
        self._request = requests
        self._requirements = requirments
        self._th_requests = th.Thread(target=self._thread_read_requests)

    def start(self):
        self._online = True
        self._th_requests.start()
        self.to_INIT()
        while not self._online:
            self.change_state()

    def _thread_read_requests(self):
        while self._online:
            if self._pipe.poll():
                recv = self._pipe.recv()
                if isinstance(recv, Mapping):
                    self._requirements.set_data(recv['name'], recv['data'])
                else:
                    self._request.set_current(recv)
