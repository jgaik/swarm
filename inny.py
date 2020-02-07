import server

with server.Client() as c:
    dupa = c.read(server.READ_MARKERS)["markers"]
    print(dupa)
