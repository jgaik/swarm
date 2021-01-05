import threading as th
from collections.abc import Mapping
from swarm.shared import config
from swarm.shared.templates import data


class BaseRequirements:
    datatags = []

    def __init__(self):
        self._data = {}
        self._lock = th.Lock()
        for tag in self.datatags:
            self._data[tag] = data.LockedData()
            self._add_method_have(tag)

    def have_data(self, require_name=None):
        if require_name is None:
            return all([x.is_set() for x in self._data])
        if isinstance(require_name, list):
            return all(
                [self._data[name].is_set() for name in require_name if name in self.datatags])
        else:
            if require_name in self.datatags:
                self._data[require_name].is_set()
            else:
                return False

    def wait_data(self, require_name=None):  # needs change
        if require_name is None:
            for e in self._data:
                e.wait()
        if isinstance(require_name, list):
            for name in require_name:
                if name in self.datatags:
                    self._data[name].wait()
        else:
            if require_name in self.datatags:
                self._data[require_name].wait()
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
                if name in self.datatags:
                    tmp[name] = self._data[name].get()
        else:
            if require_name in self.datatags:
                tmp = self._data[require_name].get()
        return tmp

    def set_data(self, require_name, require_data):
        if require_name in self.datatags:
            self._data[require_name].set(require_data)

    def _add_method_have(self, name):
        def fn(self=self):
            return self._data[name].is_set()
        setattr(self, 'have_' + name, fn)

    def _add_method_wait(self, name):
        def fn(self=self):
            self._data[name].wait()
        setattr(self, 'wait_' + name, fn)


class BaseFSM(object):
    # pylint: disable=no-member, redefined-outer-name
    def __init__(self, pipe, request, requirments):
        self._online = False
        self._pipe = pipe
        self._request = request
        self._requirements = requirments
        self._th_requests = th.Thread(target=self._thread_read_requests)
        self.state = None

    def start(self):
        self._online = True
        self._th_requests.start()
        while self._online:
            self.change_state()

    def _thread_read_requests(self):
        while self._online:
            if self._pipe.poll():
                recv = self._pipe.recv()
                if isinstance(recv, Mapping):
                    self._request.set_current(recv['request'])
                    for (name, data) in recv['data']:
                        self._requirements.set_data(name, data)
                else:
                    self._request.set_current(recv)

    def send_response(self, response, data=None):
        _data = {}
        if response is config.Response.INIT:
            _data['response'] = response
            _data['name'] = __name__
            _data['requirements'] = self._requirements.datatags
            if not data is None:
                _data['data'] = data
        else:
            if data is None:
                _data = response
            else:
                _data['response'] = response
                _data['data'] = data
        self._pipe.send(_data)
