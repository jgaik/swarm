import time
import digi.xbee.devices as xb
import struct

ROBOTPATH_LINE = 1
ROBOTPATH_ARC = 2
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

class Robot:
	
	def __init__(self, addressString, deviceXbee):
		self.robotId = addressString.get_lsb()
		self.device = deviceXbee
		self.fields = {}

	def getDevice(self):
		return self.device
	
	def getID(self):
		return self.robotId

	def addFields(self, fieldEntries):
		pass

	def getField(self, fieldKey):
		pass

	@classmethod
	def createFromList(cls, deviceList):
		robotList = []
		for dev in deviceList:
			robotList.append(cls(dev.get_16bit_addr(), dev))
		return robotList

	@staticmethod
	def getDeviceFromList(robotList, robotID) -> xb.RemoteXBeeDevice:
		for rbt in robotList:
			if rbt.getID() == robotID:
				return rbt.getDevice()
		raise Exception(f"!!![Xbee Network]: Unknown robot address ({robotID})!!!")

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
		self.xbDevice.add_data_received_callback(self.recvDataCallback)
		self.xbNet = self.xbDevice.get_network()
		self.updateNetwork()
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
			self.robotList = Robot.createFromList(self.xbNet.get_devices())
			print(f"[Xbee Network]: {len(self.robotList)} remote device(s) found.")
		else:
			print(f"!!![Xbee Network]: Device not open!!!")
	
	def __sendData(self, data, robotID):
		msg = Message(robotID, data["mode"], data["params"])
		if robotID == ROBOTNET_BROADCAST:
			self.xbDevice.send_data_broadcast(msg())
		else:
			try:
				remote = Robot.getDeviceFromList(self.robotList, robotID)
				print(f"[Xbee Network]: Sending message: {msg()}.")
				self.xbDevice.send_data_async(remote, msg())
			except Exception as exc:
				print(exc)
	
	def recvDataCallback(self, xbeeMsg: xb.XBeeMessage):
		print(xbeeMsg.data.decode('utf-8'))
	
	def setRobotVelocity(self, robotID, pathMode, pathParameters):
		"""pathParameters order [velocity, distance/angle, radius (for arc)]"""
		if pathMode == ROBOTPATH_ARC:
			assert (len(pathParameters) == 3), f"!!![Xbee Network]: Wrong number of path parameters ({pathParameters})!!!"
		if pathMode == ROBOTPATH_LINE:
			assert (len(pathParameters) == 2), f"!!![Xbee Network]: Wrong number of path parameters ({pathParameters})!!!"
		data = {}
		data["mode"] = pathMode
		data["params"] = []

		for pIdx in range(len(pathParameters)):
			data["params"].append([pIdx, pathParameters[pIdx]])
		
		self.__sendData(data, robotID)