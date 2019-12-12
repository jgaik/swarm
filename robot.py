import time
import digi.xbee.devices as xb
import struct

ROBOTPATH_LINE = 1
ROBOTPATH_ARC = 2
ROBOTPATH_TURN = 3
ROBOTPATH_VELOCITY = 4
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
			msgParts.append(struct.pack("B", param[0]) + struct.pack(">f", param[1]))
		
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

	def __init__(self, xbeeList):
		self.ids = []
		self.devices = []
		self.status = []
		for dev in xbeeList:
			self.ids.append(dev.get_16bit_addr().get_lsb())
			self.devices.append(dev)
			self.status.append(ROBOTSTATUS_IDLE)

	def __call__(self, robotId) -> xb.RemoteXBeeDevice:
		try:
			return self.devices[self.ids.index(robotId)]
		except ValueError:
			print(f"[Xbee Network]: !!!Unknown robot address ({robotId})!!!")

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


class RobotNetwork:
	xbPortnum = "/dev/ttyUSB0"
	xbBaudrate = "9600"
	xbNetDiscoveryTimeOut = 5

	def __init__(self, portnum = xbPortnum, baudrate = xbBaudrate):
		self.xbBaudrate = baudrate
		self.xbPortnum = portnum
		self.xbDevice = xb.XBeeDevice(self.xbPortnum, self.xbBaudrate)
		self.xbRemotes = None
	
	def __enter__(self):
		print("[Xbee network]: Initialising..")
		self.xbDevice.open()
		self.xbNet = self.xbDevice.get_network()
		self.updateNetwork()
		self.xbDevice.add_data_received_callback(self.recvDataCallback)
		print(f"[Xbee Network]: Initialisation finished.")
		return self

	def __exit__(self, _, __, ___):
		self.xbDevice.del_data_received_callback(self.recvDataCallback)
		self.xbDevice.close()
		print("[Xbee Network]: Connection closed.")

	def updateNetwork(self, discoveryTimeOut = xbNetDiscoveryTimeOut):
		if self.xbDevice._is_open:
			print(f"[Xbee Network]: Network discovery process.")
			self.xbNet.set_discovery_timeout(float(discoveryTimeOut))
			self.xbNet.start_discovery_process()
			while self.xbNet.is_discovery_running():
				time.sleep(0.5)
				print(".")
			self.robotList = RobotList(self.xbNet.get_devices())
			print(f"[Xbee Network]: {self.robotList.getLength()} remote device(s) found.")
		else:
			print(f"[Xbee Network]: !!!Device not open!!!")
	
	def __sendData(self, data, robotID):
		msg = Message(robotID, data["mode"], data["params"])
		if robotID == ROBOTNET_BROADCAST:
			self.xbDevice.send_data_broadcast(msg())
		else:
			try:
				remote = self.robotList(robotID)
				print(f"[Xbee Network]: Sending message: {msg()}.")
				self.xbDevice.send_data_async(remote, msg())
			except:
				print(f"[Xbee Network]: !!!Error sending the data to device {robotID}!!!")
	
	def recvDataCallback(self, xbeeMsg: xb.XBeeMessage):
		id = xbeeMsg.remote_device.get_16bit_addr().get_lsb()
		self.robotList.setStatus(id, xbeeMsg.data.decode('utf-8'))
		""" try:
			if (len(xbeeMsg.data.decode('utf-8')) == 1):
				sender = next((x for x in self.robotList if x.getId() == id))
				sender.changeStatus(xbeeMsg.data.decode('utf-8'))
			
		except:
			print(f"[Xbee Network]: !!!Error while receiving the data from {id}!!!") """
		
		print(f"Robot {id} data:")
		print(xbeeMsg.data.decode('utf-8'))
	
	def setRobotVelocity(self, robotID, pathMode, pathParameters):
		"""Set velocities of the 'robotID' robot
		:param pathMode: path mode of the setting
		:param pathParameters: parameters in order:
			_LINE [time, distance]
			_ARC [time, angle distance, radius]
			_TURN [time, angle distance]
			_VELOCITY [velocityLeft, velocityRight]
		"""
		if pathMode == ROBOTPATH_ARC:
			assert (len(pathParameters) == 3), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
			assert (pathParameters[2] != 0 ), f"[Xbee Network]: !!!Incorect parameter - arc radius cannot be 0!!!"
		if pathMode == ROBOTPATH_LINE:
			assert (len(pathParameters) == 2), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
		if pathMode == ROBOTPATH_TURN:
			assert (len(pathParameters) == 2), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
		if pathMode == ROBOTPATH_VELOCITY:
			assert (len(pathParameters) == 2), f"[Xbee Network]: !!!Wrong number of path parameters ({pathParameters})!!!"
		data = {}
		data["mode"] = pathMode
		data["params"] = []

		for pIdx in range(len(pathParameters)):
			data["params"].append([pIdx, pathParameters[pIdx]])
		
		self.__sendData(data, robotID)