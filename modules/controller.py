import server
import robot
import tasks
import time
import numpy as np

CODELIST = {
	'Line': robot.ROBOTPATH_LINE,
	'Turn': robot.ROBOTPATH_TURN,
	'Arc': robot.ROBOTPATH_ARC,
	'Velocity': robot.ROBOTPATH_VELOCITY
}

def marker():
	markers = np.array([[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [181.5, 157.5, 0.0, 1.0], [0.0, 0.0, 0.0, 0.0], [208.75, 23.75, -1.8018869939907933, 1.0], [186.5, 119.5, -1.3854483767992019, 1.0], [0.0, 0.0, 0.0, 0.0], [222.0, 163.5, 1.508377516798939, 1.0], [181.0, 200.0, 2.6224465393432705, 1.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [88.75, 75.5, 0.5713374798336268, 1.0], [143.75, 178.25, -0.6947382761967034, 1.0], [128.75, 35.75, 0.540419500270584, 1.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [91.5, 231.25, -2.782821983319221, 1.0], [0.0, 0.0, 0.0, 0.0]])
	markers[:,0]=markers[:,0]/362*200
	markers[:,1]=(298-markers[:,1])/298*160
	markers[:,0:3]=np.round(markers[:,0:3],3)
	return markers.tolist()

class Controller():

	def __init__(self, netPort, netBaudrate, camIp, camPort):
		self._online = False
		self._active = False
		self._swarm = robot.RobotNetwork(netPort, netBaudrate)
		self._camera = server.Client(camIp, camPort)
		self._markers = {}
		self._commandReady = False
		self._commandData = {}

	def run(self):
		with self._swarm, self._camera:
			self._online = True
			while self._active:
				self._markers = self._camera.read(server.READ_MARKERS)['markers']
				if self._commandReady:
					if self._commandData['task'] == "Direct control":
						self._commandData['data']['pathMode'] = CODELIST[self._commandData['data']['pathMode']]
						self._swarm.setRobotVelocity(**self._commandData['data'])
					if self._commandData['task'] == 'Parameters setting':
						self._swarm.setRobotParameters(**self._commandData['data'])
					self._commandReady = False

		self._online = False
	
	def getMarkers(self) -> str:
		return self._markers

	def getIds(self):
		return self._swarm.robotList.getIds()

	def getIDs(self):
		if self._online:
			return self._swarm.robotList.getIds()

	def setData(self, data):
		if not self._commandReady:
			self._commandData = data
			self._commandReady = True

	def isOnline(self):
		return self._online

	def start(self):
		self._active = True

	def stop(self):
		self._active = False