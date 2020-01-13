import server
import robot
import tasks
import time

def main():
	
	with robot.RobotNetwork() as swarmNet:
		tstart = time.monotonic()
		while True:
			if (time.monotonic() - tstart > 5):
				swarmNet.setRobotVelocity(1, robot.ROBOTPATH_LINE, [3, 300])
				tstart = time.monotonic()


if __name__ == "__main__":
	main()