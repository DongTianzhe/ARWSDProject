import socket
import json

socketServer = socket.socket()

socketServer.bind(('localhost', 56001))
socketServer.listen(1)

conn, address = socketServer.accept()
print(f'Received. Address: {address}')

while True:
    data = conn.recv(4096).decode('utf-8')
    print(data)
    msg = input(':')
    if msg == 'exit':
        break

d = json.loads(data)
print(d.get("type"), d.get("config"))

conn.close()
socketServer.close()