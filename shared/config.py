import enum
import threading as th


class BaseRequestResponse:

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

    def is_new(self):
        return self._event_new.is_set()

    def wait_new(self):
        self._event_new.wait()
        self._event_new.clear()

    def _add_method_is(self, name):
        def fn(self=self):
            return self._events[name].is_set()
        setattr(self, 'is_' + name, fn)

    def _add_method_wait(self, name):
        def fn(self=self):
            self._events[name].wait()
        setattr(self, 'wait_' + name, fn)


class Request(BaseRequestResponse):
    INIT = enum.auto()
    END = enum.auto()
    DO = enum.auto()
    READ = enum.auto()


class Response(BaseRequestResponse):
    INIT = enum.auto()
    ERROR = enum.auto()
    OK = enum.auto()
    READY = enum.auto()
