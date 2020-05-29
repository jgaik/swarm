import time
from typing import List
from threading import Thread
import digi.xbee.devices as xb
import struct

ROBOTPATH_LINE = 1
ROBOTPATH_ARC = 2
ROBOTPATH_TURN = 3
ROBOTPATH_VELOCITY = 4

ROBOTMODE_INIT = 5
ROBOTNET_BROADCAST = 255

ROBOTSTATUS_IDLE = 0
ROBOTSTATUS_REC_OK = 1
ROBOTSTATUS_REC_ERR = 2


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


class RobotList:

    def __init__(self):
        self.ids = []
        self.devices = []
        self.status = []
        self.buffer = []

    def getDevice(self, robotId) -> xb.RemoteXBeeDevice:
        try:
            return self.devices[self.ids.index(robotId)]
        except ValueError:
            print(f"[Xbee Network]: !!!Unknown robot address ({robotId})!!!")

    def addDevice(self, xbeeDevice: xb.RemoteXBeeDevice):
        if not self.checkId(xbeeDevice.get_16bit_addr().get_lsb()):
            self.ids.append(xbeeDevice.get_16bit_addr().get_lsb())
            self.devices.append(xbeeDevice)
            self.status.append(ROBOTSTATUS_IDLE)
            self.buffer.append('')
            print(
                f"[Xbee Network]: Robot {xbeeDevice.get_16bit_addr().get_lsb()} added to list")

    def addDevices(self, xbeeList: List[xb.RemoteXBeeDevice]):
        for dev in xbeeList:
            self.ids.append(dev.get_16bit_addr().get_lsb())
            self.devices.append(dev)
            self.status.append(ROBOTSTATUS_IDLE)
            self.buffer.append('')

    def getStatus(self, robotId):
        try:
            return self.status[self.ids.index(robotId)]
        except ValueError:
            print(f"[Xbee Network]: !!!Unknown robot address ({robotId})!!!")

    def setStatus(self, robotId, statusCode):
        assert (statusCode in [ROBOTSTATUS_IDLE, ROBOTSTATUS_REC_ERR, ROBOTSTATUS_REC_OK]),\
            f"[Xbee Network]: !!!Unknown status code!!!"
        try:
            self.status[self.ids.index(robotId)] = statusCode
        except ValueError:
            print(f"[Xbee Network]: !!!Unknown robot address ({robotId})!!!")

    def getLength(self):
        return len(self.ids)

    def getIds(self):
        return self.ids

    def checkId(self, robotId):
        return robotId in self.ids


class RobotNetwork:
    xbPortnum = "/dev/ttyUSB0"
    xbBaudrate = "9600"
    xbNetDiscoveryTimeOut = 3.2

    def __init__(self, portnum=xbPortnum, baudrate=xbBaudrate):
        self.xbBaudrate = baudrate
        self.xbPortnum = portnum
        self.xbDevice = xb.XBeeDevice(self.xbPortnum, self.xbBaudrate)
        self.xbRemotes = None
        self.robotList = RobotList()

    def __enter__(self):
        print("[Xbee network]: Initialising..")
        self.xbDevice.open()
        self.xbNet = self.xbDevice.get_network()
        self.xbDevice.add_data_received_callback(self.__callbackDataRecv)
        self.__updateNetworkThread()
        print(f"[Xbee Network]: Initialisation finished.")
        # Thread(target=self.__updateNetworkThread).start()
        return self

    def __exit__(self, _, __, ___):
        self.xbNet.stop_discovery_process()
        self.xbDevice.del_data_received_callback(self.__callbackDataRecv)
        self.xbDevice.close()
        print("[Xbee Network]: Connection closed.")

    def __updateNetworkThread(self):
        if self.xbDevice._is_open:
            print(f"[Xbee Network]: Network discovery process started.")
            self.xbNet.add_device_discovered_callback(
                self.__callbackDeviceFound)
            self.xbNet.start_discovery_process()
            while self.xbNet.is_discovery_running():
                pass
        else:
            print(f"[Xbee Network]: !!!Controller device not open!!!")

    def __sendData(self, data, robotID):
        msg = Message(robotID, data["mode"], data["params"])
        if robotID == ROBOTNET_BROADCAST:
            self.xbDevice.send_data_broadcast(msg())
        else:
            try:
                remote = self.robotList.getDevice(robotID)
                self.xbDevice.send_data_async(remote, msg())
                print(
                    f"[Xbee Network]: Sending message: {' '.join([str(m) for m in msg()])}")
            except:
                print(
                    f"[Xbee Network]: !!!Error sending the data to device {robotID}!!!")

    def __callbackDataRecv(self, xbeeMsg: xb.XBeeMessage):
        id = xbeeMsg.remote_device.get_16bit_addr().get_lsb()
        msg = xbeeMsg.data.decode('utf-8')

        print(f"(Robot {id}): {msg}")

    def __callbackDeviceFound(self, xbeeRemote: xb.RemoteXBeeDevice):
        id = xbeeRemote.get_16bit_addr().get_lsb()
        print(f"[Xbee Network]: Robot {id} found")
        self.robotList.addDevice(xbeeRemote)
        self.setRobotParameters(id)

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
        if pathMode == ROBOTPATH_ARC:
            assert (len(pathParameters) ==
                    3), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
            assert (
                pathParameters[2] != 0), f"[Xbee Network]: !!!Incorect parameter - arc radius cannot be 0!!!"
        if pathMode == ROBOTPATH_LINE:
            assert (len(pathParameters) ==
                    2), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
        if pathMode == ROBOTPATH_TURN:
            assert (len(pathParameters) ==
                    2), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
        if pathMode == ROBOTPATH_VELOCITY:
            assert (len(pathParameters) ==
                    3), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
        data = {
            "mode": pathMode,
            "params": []
        }

        for pIdx in range(len(pathParameters)):
            data["params"].append([pIdx, pathParameters[pIdx]])

        self.__sendData(data, robotID)

    def setRobotParameters(self, robotID, distance=None, radiusLeft=None, radiusRight=None, pid=None):
        """
        Set parameters of the 'robotID' robot
        :param distance: distance between the centers of the wheels
        :param radiusLeft: radius of the left wheel
        :param radiusRight: radius of the right wheel
        :param pid: list of pid controller gain values [kp, ki, kd]
        """

        data = {
            "mode": ROBOTMODE_INIT,
            "params": []
        }
        if (distance is not None):
            assert (
                distance > 0), f"[Xbee Network]: !!!Wheel distance must be bigger than 0!!!"
            data["params"].append([0, distance])
        if (radiusLeft is not None):
            assert (
                radiusLeft > 0), f"[Xbee Network]: !!!Wheel radius must be bigger than 0!!!"
            data["params"].append([1, radiusLeft])
        if (radiusRight is not None):
            assert (
                radiusRight > 0), f"[Xbee Network]: !!!Wheel radius must be bigger than 0!!!"
            data["params"].append([2, radiusRight])
        if (pid is not None):
            assert (len(
                pid) == 3), f"[Xbee Network]: !!!PID controller parameters must be of length 3!!!"
            for val in range(3):
                data["params"].append([val + 3, pid[val]])

        self.__sendData(data, robotID)
