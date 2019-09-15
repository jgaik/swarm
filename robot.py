import digi.xbee.devices as xb

class Robot:
    xbeePortnum = "/dev/ttyUSB0"
    xbeeBaudrate = "9600"

    def __init__(self, portnum = xbeePortnum, baudrate = xbeeBaudrate):
        self.xbeeBaudrate = baudrate
        self.xbeePortnum = portnum
        self.xbeeDevice = xb.XBeeDevice(self.xbeePortnum, self.xbeeBaudrate)
    
    def __enter__(self):
        self.xbeeDevice.open()

    def __exit__(self, _, __, ___):
        self.xbeeDevice.close()
