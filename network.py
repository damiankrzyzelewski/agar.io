import socket

class Network:

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "localhost"
        self.port = 5555
        self.addr = (self.host, self.port)
        self.id = self.connect()

    def connect(self):
        self.client.connect(self.addr)
        return self.client.recv(2048).decode()

    def send(self, data):
        try:
            self.client.sendall(str.encode(data))
            reply = self.client.recv(2048).decode()

            if ":" in reply:
                return reply
            else:
                return "Invalid server response"

        except socket.error as e:
            return str(e)

    def receive(self):
        try:
            return self.client.recv(2048).decode()
        except socket.error as e:
            print(e)
