import time
import digi.xbee.devices as xb

BROADCAST = -1

class Robot:
  xbPortnum = "/dev/ttyUSB0"
  xbBaudrate = "9600"
  xbNetDiscoveryTimeOut = 10

  def __init__(self, portnum = xbPortnum, baudrate = xbBaudrate):
    self.xbBaudrate = baudrate
    self.xbPortnum = portnum
    self.xbDevice = xb.XBeeDevice(self.xbPortnum, self.xbBaudrate)
    self.xbRemotes = None

    self.robotNames = {}
    for idx in range(0, 1):
      self.robotNames[str(idx)] = f"Robot {idx}"
  
  def __enter__(self):
    print("[Xbee network]: Initialising..")
    self.xbDevice.open()
    self.xbNet = self.xbDevice.get_network()
    self.xbNet.set_discovery_timeout(self.xbNetDiscoveryTimeOut)
    self.xbNet.start_discovery_process()
    while self.xbNet.is_discovery_running():
      time.sleep(0.5)
      print(".")
    self.xbRemotes = self.xbNet.get_devices()
    print(f"[Xbee Network]: Initialisation finished.")
    print(f"[Xbee Network]: {len(self.xbRemotes)} remote devices found.")

  def __exit__(self, _, __, ___):
    self.xbDevice.close()

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