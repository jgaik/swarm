import server
import tasks

def main():
	with server.Client() as client:
		while True:
			print(client.read(server.READ_MARKERS))


if __name__ == "__main__":
	main()