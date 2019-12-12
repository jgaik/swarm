import server
import robot
import tasks

def main():
	with robot.RobotNetwork() as swarmNet:
		while (swarmNet.robotList.getStatus(1) == robot.ROBOTSTATUS_IDLE):
			swarmNet.setRobotVelocity(1, robot.ROBOTPATH_LINE, [0.20, 200])
		while True:
			pass


if __name__ == "__main__":
	main()