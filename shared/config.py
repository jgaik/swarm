import enum
from swarm.shared.templates import data


class Request(data.BaseRequestResponse):
    INIT = enum.auto()
    END = enum.auto()
    DO = enum.auto()
    READ = enum.auto()


class Response(data.BaseRequestResponse):
    INIT = enum.auto()
    ERROR = enum.auto()
    OK = enum.auto()
    READY = enum.auto()
    END = enum.auto()
