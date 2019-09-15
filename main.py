import server
import tasks

def main():
	client = server.Client()
	with client:
		while True:
			client.read(server.READ_MARKERS)

if __name__ == "__main__":
	main()