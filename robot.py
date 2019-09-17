import time
import digi.xbee.devices as xb

ROBOTNAME_IDX = (0, 0)
BROADCAST = -1

class RobotNetwork:
  xbPortnum = "/dev/ttyUSB0"
  xbBaudrate = "9600"
  xbNetDiscoveryTimeOut = 10

  def __init__(self, portnum = xbPortnum, baudrate = xbBaudrate):
    self.xbBaudrate = baudrate
    self.xbPortnum = portnum
    self.xbDevice = xb.XBeeDevice(self.xbPortnum, self.xbBaudrate)
    self.xbRemotes = None

    self.robotNames = {}
    for idx in range(ROBOTNAME_IDX[0], ROBOTNAME_IDX[1] + 1):
      self.robotNames[str(idx)] = f"Robot {idx}"
  
  def __enter__(self):
    print("[Xbee network]: Initialising..")
    self.xbDevice.open()
    self.xbNet = self.xbDevice.get_network()
    self.updateNetwork()
    print(f"[Xbee Network]: Initialisation finished.")
    return self

  def __exit__(self, _, __, ___):
    self.xbDevice.close()

  def updateNetwork(self, discoveryTimeOut = xbNetDiscoveryTimeOut):
    if self.xbDevice._is_open():
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
  
  def sendData(self, data, id = BROADCAST):
    if id == BROADCAST:
      self.xbDevice.send_data_broadcast(data)
    elif str(id) not in self.robotNames:
      remote = self.xbNet.get_device_by_node_id(self.robotNames[str(id)])
      if remote is not None:
        self.xbDevice.send_data_async(remote, data)
      else:
        print(f"[Xbee Network]: {self.robotNames[str(id)]} is not detected.")
    else:
      print(f"[Xbee Network]: Unknown id ({id}).")