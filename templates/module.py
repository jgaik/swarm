import threading as th


class Requirements:
    modulelist = []

    def __init__(self):
        self._data = {}
        self._lock = th.RLock()
        for ml in self.modulelist:
            self._data[ml] = None

    def have_data(self, require_name):
        if require_name in self.modulelist:
            with self._lock:
                return not self._data is None
        else:
            return False

    def get_data(self, require_name):
        if not require_name in self.modulelist:
            return None
        with self._lock:
            tmp = self._data[require_name]
            self._data[require_name] = None
        return tmp

    def set_data(self, require_name, require_data):
        if require_name in self.modulelist:
            with self._lock:
                self._data[require_name] = require_data


class Requests:

    def __init__(self):
        self._current = None
        self._lock = th.RLock()

    def set_current(self, request):
        with self._lock:
            self._current = request

    def get_current(self):
        with self._lock:
            tmp = self._current
            self._current = None
        return tmp

    def is_request(self, request):
        with self._lock:
            return self._current == request

    def is_new(self):
        with self._lock:
            return not self._current is None
