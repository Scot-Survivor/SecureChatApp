import socket
import ssl
import select

from threading import Thread, Event
from server_login import login


class LoginError(Exception):
    pass


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
    def __init__(self, given_email, given_password, client_socket, client_address, connection, cursor):
        self.cursor = cursor
        self.connection = connection
        self.socket = client_socket
        self.address = client_address
        self.client_username, self.tag, self.userid = self.__login(given_email, given_password)
        pass

    def kick(self):
        pass

    @property
    def client_connection(self):  # return the __connection object and ip in port with tuple (object, (IP, PORT))
        return self.socket, (self.address[0], self.address[1])

    @property
    def username(self):
        return self.client_username + '#' + str(self.tag)

    def __login(self, user_email, user_password):
        if login(user_password=user_password, username=user_email, c=self.cursor):
            return True
        else:
            raise LoginError("Invalid Password or Username")


class Server:
    def __init__(self, ip, port, header_length):
        # Initialise the self constants
        self.__ip = ip
        self.__port = port
        self.HEADER_LENGTH = header_length

        # Create the context for SSL
        self.__context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.__context.load_cert_chain("cert.pem")
        self.__context.check_hostname = 0
        self.__context.verify_mode = 0

        # Database initialisation will go here in the future

        # Initialise the __active_sockets

        __server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket_ssl = self.__context.wrap_socket(__server_socket, server_side=True)

        self.socket_ssl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket_ssl.bind((self.__ip, self.__port))  # Bind the set IP and PORT
        self.socket_ssl.listen(
            10)  # Listen for connections. The number is the how many connections can be in the list at once before .accept() is called

        self.__clients = []
        self.__active_sockets = [self.socket_ssl]

        self.__connection, self.c = None, None  # TODO Setup Database(Planning on remote MySQL) and connect to said database
        self.AcceptingThread = StoppableThread(target=self.__active_sockets)

    def accept_new_connections(self):
        read_sockets, _, exception_sockets = select.select(self.__active_sockets, [], self.__active_sockets)
        for waiting_socket in read_sockets:
            if waiting_socket == self.socket_ssl:
                client_socket, client_address = self.socket_ssl.accept()
                # noinspection PyNoneFunctionAssignment,PyTupleAssignmentBalance
                email, password = self.__grab_user(client_socket)
                try:
                    new_client = Client(given_email=email, given_password=password,
                                        client_socket=client_socket, client_address=client_address,
                                        connection=self.__connection, cursor=self.c)
                except LoginError:
                    pass  # TODO Kill the connection
                else:
                    self.__clients.append(new_client)
                    self.__active_sockets.append(client_socket)

    def __grab_user(self, client_socket):
        pass
