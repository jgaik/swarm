import time
import digi.xbee.devices as xb

BROADCAST = -1

class Robot:
  
  def __init__(self, addressString, deviceXbee):
    self.robotAddress = xb.XBee16BitAddress.from_hex_string(addressString)
    self.device = deviceXbee
    self.fields = {}

  def getDevice(self):
    return self.device
  
  def getAddress(self):
    return self.robotAddress

  def addFields(self, fieldEntries):
    pass

  def getField(self, fieldKey):
    pass

  @classmethod
  def createFromList(cls, stringList):
    pass

  @staticmethod
  def getDeviceFromList(robotList, addressString):
    pass

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

  def updateNetwork(self, discoveryTimeOut = xbNetDiscoveryTimeOut):
    if self.xbDevice._is_open:
      print(f"[Xbee Network]: Network discovery process.")
      self.xbNet.set_discovery_timeout(self.xbNetDiscoveryTimeOut)
      self.xbNet.start_discovery_process()
      while self.xbNet.is_discovery_running():
        time.sleep(0.5)
        print(".")
      self.xbRemotes = self.xbNet.get_devices()
      print(f"[Xbee Network]: {len(self.xbRemotes)} remote devices found.")
    else:
      print(f"[Xbee Network]: Device not open.")
  
  def sendData(self, data, robotAddress = BROADCAST):
    if robotAddress == BROADCAST:
      self.xbDevice.send_data_broadcast(data)
    else:
      remote = self.xbNet.get_device_by_16(xb.XBee16BitAddress.from_hex_string(str(robotAddress)))
      if remote is not None:
        self.xbDevice.send_data_async(remote, data)
      else:
        print(f"[Xbee Network]: Unknown robotAddress ({robotAddress}).")
  
  def recvDataCallback(self, xbeeMsg):
    pass