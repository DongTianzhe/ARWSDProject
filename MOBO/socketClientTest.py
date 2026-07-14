import socket
import json
import time

with open('InitialisationConfiguration.json', encoding='utf-8') as f:
    data = json.load(f)

socketClient = socket.socket()
socketClient.connect(('localhost', 56001))

socketClient.send(json.dumps(data).encode('utf-8'))
socketClient.send('\n'.encode('utf-8'))

print(data)

time.sleep(5)
socketClient.close()