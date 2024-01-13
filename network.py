import socket

class Network:
    """
    Klasa Network reprezentuje połączenie z serwerem w grze. Zarządza gniazdem (socket),
    umożliwia nawiązywanie połączenia, wysyłanie i odbieranie danych od serwera.
    """
    def __init__(self):
        """
        Inicjalizuje obiekt klasy Network, ustawiając gniazdo, adres serwera i port.
        Nawiązuje połączenie z serwerem i odbiera identyfikator przydzielony klientowi.
        """
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "localhost"
        self.port = 5555
        self.addr = (self.host, self.port)
        self.id = self.connect()

    def connect(self):
    # Nawiązuje połączenie z serwerem, wysyła żądanie i odbiera identyfikator klienta.
        self.client.connect(self.addr)
        return self.client.recv(2048).decode()

    def send(self, data):
    # Wysyła dane do serwera i odbiera odpowiedź. Sprawdza poprawność odpowiedzi.
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
    # Odbiera dane od serwera.
        try:
            return self.client.recv(2048).decode()
        except socket.error as e:
            print(e)
