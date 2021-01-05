import threading as th


class LockedData:

    def __init__(self, single_use=True, data=None):
        self._event_new = th.Event()
        self._event_data = th.Event()
        self._lock = th.Lock()
        self._data = data
        self._mode_single = single_use

    def is_set(self):
        return self._event_data.is_set()

    def is_new(self):
        if self._mode_single:
            return self.is_set()
        else:
            return self._event_new.is_set()

    def wait(self, timeout=None):
        self._event_data.wait(timeout)

    def wait_new(self, timeout=None):
        if self._mode_single:
            self.wait(timeout)
        else:
            self._event_new.wait(timeout)

    def set(self, data):
        with self._lock:
            self._data = data
        if self._mode_single:
            self._event_data.set()
        else:
            self._event_data.set()
            self._event_new.set()

    def get(self):
        try:
            if self._event_data.is_set():
                with self._lock:
                    return self._data
            else:
                return None
        finally:
            if self._mode_single:
                self._event_data.clear()
            else:
                self._event_new.clear()


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
