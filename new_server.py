import socket
import ssl

from threading import Thread, Event

# Initialise the global constants
HEADER_LENGTH = 10
IP = "0.0.0.0"
PORT = 1234

# Create the context for SSL
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("cert.pem")
context.check_hostname = 0
context.verify_mode = 0

# Database initialisation will go here in the future


# Initialise the sockets

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket_ssl = context.wrap_socket(server_socket, server_side=True)

server_socket_ssl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket_ssl.bind((IP, PORT))  # Bind the set IP and PORT
server_socket_ssl.listen(
    10)  # Listen for connections. The number is the how many connections can be in the list at once before .accept() is called

socket_list = [server_socket_ssl]

clients = {}
usernames = []


# https://stackoverflow.com/a/325528
class StoppableThread(Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self):
        raise Exception(f"Thread Killed. {self.getName()}")

    def stopped(self):
        return self._stop_event.is_set()


class Client:  # This class is for every client that connects. Stores some important information and groups functions together.
    def __init__(self, given_username, password, client_socket):
        pass

    def kick(self): pass

    @property
    def connection(self):  # return the connection object and ip in port with tuple (object, (IP, PORT))
        pass
