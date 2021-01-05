import enum
from typing import List
import threading as th
import struct
import transitions
import digi.xbee.devices as xb
from swarm.shared import config
from swarm.shared.templates import modules


class RobotParameters:

    def __init__(self, distance=None, radiusLeft=None, radiusRight=None, pid=None):
        self.distance = distance
        self.radiusLeft = radiusLeft
        self.radiusRight = radiusRight
        self.pid = pid

    def __iter__(self):
        yield from [self.distance, self.radiusLeft, self.radiusRight, self.pid]


class RobotPath(enum.Enum):
    LINE = 1
    ARC = 2
    TURN = 3
    VELOCITY = 4


class RobotStatus(enum.Enum):
    INIT = -1
    IDLE = 0
    REC_OK = 1
    REC_ERR = 2


ROBOTMODE_INIT = 5
ROBOTNET_BROADCAST = 255


class Message:
    _header = '*'
    _modulo = 256
    _msg = b''

    def __init__(self, robotID, mode, parametersList):
        self.robotID = robotID
        self.mode = mode
        self.parameters = parametersList
        msgLength = len(parametersList) * 5 + 1
        msgParts = []
        msgParts.append(self._header.encode('utf-8'))
        msgParts.append(struct.pack("B", robotID))
        msgParts.append(struct.pack("B", mode))
        msgParts.append(struct.pack("B", msgLength))
        for param in parametersList:
            msgParts.append(struct.pack(
                "B", param[0]) + struct.pack(">f", param[1]))

        self._msg = b''.join(msgParts)
        self._msg = self._msg + struct.pack("B", self.getCheckSum())

    def __call__(self):
        return self._msg

    def getCheckSum(self):
        return self._modulo - sum(bytearray(self._msg)[1:]) % self._modulo - 1

    @classmethod
    def fromArray(cls, msgArray):
        pass


class Robot:

    id = -1
    device = None
    status = -1

    def __init__(self, robot_id, device):
        self.id = robot_id
        self.device = device
        self.status = RobotStatus.INIT
        self.buffer = ''

    def update(self, buffer_new):
        self.buffer += buffer_new
        return self._check_buffer()

    def _check_buffer(self):
        pass


class RobotList:

    def __init__(self):
        self.robots = {}
        self._event_status_update = th.Event()

    def get_robot_device(self, robotId) -> xb.RemoteXBeeDevice:
        try:
            return self.robots[robotId].device
        except ValueError:
            print(f"[Xbee Network]: !!!Unknown robot address ({robotId})!!!")

    def add_robot(self, xbeeDevice: xb.RemoteXBeeDevice):
        if not self.check_id(xbeeDevice.get_16bit_addr().get_lsb()):
            robot_id = xbeeDevice.get_16bit_addr().get_lsb()
            self.robots[id] = Robot(robot_id, xbeeDevice)
            print(
                f"[Xbee Network]: Robot {xbeeDevice.get_16bit_addr().get_lsb()} added to list")

    def add_robots(self, xbeeList: List[xb.RemoteXBeeDevice]):
        for dev in xbeeList:
            robot_id = dev.get_16bit_addr().get_lsb()
            self.robots[id] = Robot(robot_id, dev)

    def get_robot_status(self, robotId):
        try:
            return self.robots[robotId].status
        except ValueError:
            print(f"[Xbee Network]: !!!Unknown robot address ({robotId})!!!")

    def get_status(self):
        try:
            return dict(zip(self.robots.keys(), [self.robots[x].status for x in self.robots]))
        finally:
            self._event_status_update.clear()

    def update_robot(self, robotId, buffer_new):
        try:
            if self.robots[robotId].update(buffer_new):
                self._event_status_update.set()
        except ValueError:
            print(f"[Xbee Network]: !!!Unknown robot address ({robotId})!!!")

    def get_length(self):
        return len(self.robots)

    def get_ids(self):
        return self.robots.keys()

    def check_id(self, robotId):
        return robotId in self.robots.keys()

    def is_updated(self):
        return self._event_status_update.is_set()

    def wait_update(self):
        self._event_status_update.wait()


class RobotNetwork:
    xbNetDiscoveryTimeOut = 5

    def __init__(self, robotlist):
        self.robotList = robotlist
        self.xbDevice = None
        self.xbNet = None

    def connect(self, portnum, baudrate):
        print("[Xbee network]: Initialising..")
        self.xbDevice = xb.XBeeDevice(portnum, baudrate)
        try:
            self.xbDevice.open()
            self.xbNet = self.xbDevice.get_network()
            self.xbDevice.add_data_received_callback(self.__callbackDataRecv)
            self.xbNet.add_device_discovered_callback(
                self.__callbackDeviceFound)
            self.xbNet.set_discovery_timeout(self.xbNetDiscoveryTimeOut)
            self.xbNet.start_discovery_process()
            while self.xbNet.is_discovery_running():
                pass
            print("[Xbee Network]: Initialisation finished.")
            return True
        except:
            return False

    def disconnect(self):
        self.xbDevice.del_data_received_callback(self.__callbackDataRecv)
        self.xbDevice.close()
        print("[Xbee Network]: Connection closed.")

    def __updateNetworkThread(self):
        if self.xbDevice.is_open():
            print("[Xbee Network]: Network discovery process started.")
            while self.xbNet.is_discovery_running():
                pass
        else:
            print("[Xbee Network]: !!!Controller device not open!!!")

    def __sendData(self, data, robotID):
        msg = Message(robotID, data["mode"], data["params"])
        if robotID == ROBOTNET_BROADCAST:
            self.xbDevice.send_data_broadcast(msg())
        else:
            try:
                remote = self.robotList.get_robot_device(robotID)
                self.xbDevice.send_data_async(remote, msg())
                print(
                    f"[Xbee Network]: Sending message: {' '.join([str(m) for m in msg()])}")
                return True
            except:
                print(
                    f"[Xbee Network]: !!!Error sending the data to device {robotID}!!!")
                return False

    def __callbackDataRecv(self, xbeeMsg: xb.XBeeMessage):
        idx = xbeeMsg.remote_device.get_16bit_addr().get_lsb()
        msg = xbeeMsg.data.decode('utf-8')
        self.robotList.update_robot(idx, msg)

    def __callbackDeviceFound(self, xbeeRemote: xb.RemoteXBeeDevice):
        idx = xbeeRemote.get_16bit_addr().get_lsb()
        print(f"[Xbee Network]: Robot {idx} found")
        self.robotList.add_robot(xbeeRemote)
        self.setRobotParameters(idx)

    def setRobotVelocity(self, robotID, pathMode, pathParameters):
        """
        Set velocities of the 'robotID' robot
        :param pathMode: path mode of the setting
        :param pathParameters: parameters in order:
                ROBOTPATH_LINE [time, distance (mm)]
                ROBOTPATH_ARC [time, angle distance (radians), radius (mm)]
                ROBOTPATH_TURN [time, angle distance (radians)]
                ROBOTPATH_VELOCITY [time, velocityLeft (-1.0 to 1.0), velocityRight (-1.0 to 1.0)]
        """
        if pathMode == RobotPath.ARC:
            assert (len(pathParameters) ==
                    3), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
            assert (pathParameters[2] !=
                    0), "[Xbee Network]: !!!Incorect parameter - arc radius cannot be 0!!!"
        if pathMode == RobotPath.LINE:
            assert (len(pathParameters) ==
                    2), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
        if pathMode == RobotPath.TURN:
            assert (len(pathParameters) ==
                    2), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
        if pathMode == RobotPath.VELOCITY:
            assert (len(pathParameters) ==
                    3), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
        data = {
            "mode": pathMode,
            "params": []
        }

        for pIdx, pParams in enumerate(pathParameters):
            data["params"].append([pIdx, pParams])

        return self.__sendData(data, robotID)

    def setRobotParameters(self, robotID, robotParams=None):
        """
        Set parameters of the 'robotID' robot
        :param distance: distance between the centers of the wheels
        :param radiusLeft: radius of the left wheel
        :param radiusRight: radius of the right wheel
        :param pid: list of pid controller gain values [kp, ki, kd]
        """
        (distance, radiusLeft, radiusRight, pid) = robotParams
        data = {
            "mode": ROBOTMODE_INIT,
            "params": []
        }
        if distance is not None:
            assert (
                distance > 0), "[Xbee Network]: !!!Wheel distance must be bigger than 0!!!"
            data["params"].append([0, distance])
        if radiusLeft is not None:
            assert (
                radiusLeft > 0), "[Xbee Network]: !!!Wheel radius must be bigger than 0!!!"
            data["params"].append([1, radiusLeft])
        if radiusRight is not None:
            assert (
                radiusRight > 0), "[Xbee Network]: !!!Wheel radius must be bigger than 0!!!"
            data["params"].append([2, radiusRight])
        if pid is not None:
            assert (len(
                pid) == 3), "[Xbee Network]: !!!PID controller parameters must be of length 3!!!"
            for val in range(3):
                data["params"].append([val + 3, pid[val]])

        return self.__sendData(data, robotID)


class States(enum.Enum):
    INIT = enum.auto()
    IDLE = enum.auto()
    ERROR = enum.auto()
    CONTROL = enum.auto()
    UPDATE = enum.auto()
    END = enum.auto()


class Requirements(modules.BaseRequirements):
    datatags = ['setup_network']


class FSM(modules.BaseFSM):
    # pylint: disable=no-member
    _ok = True

    def __init__(self, pipe):
        super(FSM, self).__init__(pipe, config.Request(), Requirements())
        self.robotlist = RobotList()
        self.network = RobotNetwork(self.robotlist)

        list_transitions = [
            {
                'trigger': 'change_state',
                'source': 'none',
                'dest': States.INIT,
                'conditions': self._request.is_INIT,
            },
            {
                'trigger': 'change_state',
                'source': States.INIT,
                'dest': States.IDLE,
                'conditions': self._ok,
                'unless': False
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
                'dest': States.CONTROL,
                'conditions': True,
                'unless': False
            },
            {
                'trigger': 'change_state',
                'source': States.CONTROL,
                'dest': States.IDLE,
                'conditions': True,
                'unless': False
            },
            {
                'trigger': 'change_state',
                'source': States.IDLE,
                'dest': States.UPDATE,
                'conditions': self.robotlist.is_updated,
                'unless': False
            },
            {
                'trigger': 'change_state',
                'source': States.UPDATE,
                'dest': States.IDLE,
                'conditions': True,
                'unless': False
            }
        ]

        self.machine = transitions.Machine(model=self,
                                           states=States,
                                           transitions=list_transitions,
                                           initial='none')

    def on_enter_INIT(self):
        self.send_response(config.Response.INIT)
        self._request.wait_new()
        if self._requirements.have_data('setup_camera'):
            data = self._requirements.get_data('setup_newtowrk')
            if not self.network.connect(**data):
                self._ok = False

    def on_enter_END(self):
        self.network.disconnect()
        self.send_response(config.Response.END)

    def on_enter_ERROR(self):
        self.send_response(config.Response.ERROR)

    def on_enter_IDLE(self):
        self.send_response(config.Response.READY)

    def on_enter_CONTROL(self):
        pass

    def on_enter_UPDATE(self):
        print(self.robotlist.get_status())
