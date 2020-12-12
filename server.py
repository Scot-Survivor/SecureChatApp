import socket

import select
import ssl
import os

import server_login as login
from encryption import AESCipher
from datetime import datetime
from threading import Thread, Event

HEADER_LENGTH = 10
data_type_msg = "msg"
data_type_image = "image"

key = os.urandom(64)
print(f"[{datetime.now().strftime('%d/%m/%Y %H-%M-%S.%f')[:-2]}] {key}")
key_header = f"{len(key):<{HEADER_LENGTH}}".encode('utf-8')

cipher = AESCipher(key)
iv = cipher.returnIV()
iv_header = f"{len(iv):<{HEADER_LENGTH}}".encode('utf-8')

fmt = '%d/%m/%Y %H-%M-%S.%f'

IP = "10.147.17.168"
PORT = 1234
PORT2 = 1235

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("cert.pem")
context.check_hostname = 0
context.verify_mode = 0

server_c, server_connection = login.connect()
login.create_tables(server_c)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket_ssl = context.wrap_socket(server_socket, server_side=True)
server_socket_file_ssl = context.wrap_socket(server_socket_file, server_side=True)

server_socket_ssl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket_file_ssl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket_ssl.bind((IP, PORT))  # Bind the port and ip
server_socket_file_ssl.bind((IP, PORT2))

server_socket_ssl.listen(10)  # Begin listening for connections
server_socket_file_ssl.listen(5)

sockets_list = [server_socket_ssl, server_socket_file_ssl]  # List of active sockets

clients = {}  # Dict of the clients data.
file_clients = {}  # Dict of the clients data.

chat_history = []  # Chat History list to be sent to client. Limited to 10 for memory sake

usernames = []


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


def get_header(data):
    header = f"{len(data):<{HEADER_LENGTH}}".encode("utf-8")
    return header


# noinspection PyShadowingNames,PyBroadException
def receive_message(client_socket):
    try:
        data_type_header = client_socket.recv(HEADER_LENGTH)
        if not len(data_type_header):
            return False

        data_type_length = int(data_type_header.decode('utf-8').strip())
        data_type = client_socket.recv(data_type_length)
        if data_type.decode('utf-8') == data_type_msg:

            message_header = client_socket.recv(HEADER_LENGTH)

            if not len(message_header):
                return False
            message_length = int(message_header.decode("utf-8").strip())
            message = client_socket.recv(message_length)

            return {"data_type_header": data_type_header, "data_type": data_type, 'header': message_header,
                    "data": message}
        elif data_type.decode('utf-8') == data_type_image:
            extension_header = client_socket.recv(HEADER_LENGTH)

            if not len(extension_header):
                return False
            extension_length = int(extension_header.decode("utf-8").strip())
            extension = client_socket.recv(extension_length)

            file_header = client_socket.recv(HEADER_LENGTH)

            if not len(file_header):
                return False
            file_length = int(file_header.decode("utf-8").strip())
            file_data = b""
            while len(file_data) != file_length:
                file_data += client_socket.recv(5000000)
            return {"data_type_header": data_type_header, "data_type": data_type,
                    "extension_header": extension_header, "extension": extension,
                    "file_header": file_header, "data": file_data}

    except Exception as e:
        return False


# noinspection PyShadowingNames
def do_key_handshake(client_socket):
    # Begin Key Handshake
    client_socket.send(key_header + key)  # Send the key
    key_length = int(len(key))
    client_key = client_socket.recv(key_length)  # Receive the key from the client
    if key == client_key:
        msg = "Fine".encode("utf-8")
        msg_header = get_header(msg)
        client_socket.send(msg_header + msg)
    else:
        msg = "Key Error".encode("utf-8")
        msg_header = get_header(msg)
        client_socket.send(msg_header + msg)
        return False

    client_socket.send(iv_header + iv)  # Send IV
    iv_length = int(len(iv))
    client_iv = client_socket.recv(iv_length)
    if iv == client_iv:
        msg = "Fine".encode("utf-8")
        msg_header = get_header(msg)
        client_socket.send(msg_header + msg)
        return True
    else:
        msg = "IV Error".encode("utf-8")
        msg_header = get_header(msg)
        client_socket.send(msg_header + msg)
        return False


def format_message(client_message):
    format_codes = {
        "[b]": "[/b]",
        "[i]": "[/i]",
        "[u]": "[/u]",
        "[s]": "[/s]",
        "[sub]": "[/sub]",
        "[sup]": "[/sup]"
    }
    for code in format_codes.keys():
        end_code = format_codes.get(code)
        if code in client_message and end_code not in client_message:
            client_message += end_code

    return client_message


def run():
    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
        for notified_socket in read_sockets:
            if notified_socket == server_socket_ssl:
                client_socket, client_address = server_socket_ssl.accept()

                user = receive_message(client_socket)
                if user is False:
                    continue
                sockets_list.append(client_socket)
                clients[client_socket] = user
                username = user['data'].decode('utf-8')
                usernames.append(username)
                client_password = receive_message(client_socket)
                password = client_password['data']
                login.connect()
                new_c, new_connection = login.connect()
                check = login.login(password, username, new_c)
                if check:
                    print(
                        f"\n[{datetime.now().strftime(fmt)[:-2]}] Accepted new connection from {client_address[0]}:{client_address[1]} Username:{username} Current Connections: {len(usernames)}")
                    if do_key_handshake(client_socket):
                        print(
                            f"[{datetime.now().strftime(fmt)[:-2]}] Verified keys to {client_address[0]}:{client_address[1]}")
                        on_join(username, client_socket, cipher)
                        print(f"[{datetime.now().strftime(fmt)[:-2]}] Enter command > ", end="")
                    else:
                        print(
                            f"\n[{datetime.now().strftime(fmt)[:-2]}] Key or IV error on {client_address[0]}:{client_address[1]}")
                        print(f"[{datetime.now().strftime(fmt)[:-2]}] Enter command > ", end="")
                        continue
                elif not check:
                    print(
                        f"\n[{datetime.now().strftime(fmt)[:-2]}] Incorrect password on {client_address[0]}:{client_address[1]}")
                    print(f"[{datetime.now().strftime(fmt)[:-2]}] Enter command > ", end="")
                    pass

            elif notified_socket == server_socket_file_ssl:
                client_socket, client_address = server_socket_file_ssl.accept()

                user = receive_message(client_socket)
                if user is False:
                    continue
                file_clients[client_socket] = user

            elif notified_socket != server_socket_file_ssl or notified_socket != server_socket_ssl:
                message = receive_message(notified_socket)
                try:
                    username = clients[notified_socket]['data'].decode('utf-8')
                except KeyError:
                    try:
                        username = file_clients[notified_socket]['data'].decode('utf-8')
                    except KeyError:
                        continue

                if message is False:
                    try:
                        print(
                            f"\n[{datetime.now().strftime(fmt)[:-2]}] Closed Connection from {clients[notified_socket]['data'].decode('utf-8')} Current Connections: {len(usernames) - 1}")
                        print(f"[{datetime.now().strftime(fmt)[:-2]}] Enter command > ", end="")
                        try:
                            usernames.remove(username)
                        except Exception as e:
                            print(
                                f"\n[{datetime.now().strftime(fmt)[:-2]}] Username not removed for: " + str(
                                    e))
                            print(f"[{datetime.now().strftime(fmt)[:-2]}] Enter command > ", end="")
                        sockets_list.remove(notified_socket)
                        del clients[notified_socket]
                        continue
                    except KeyError:
                        print(
                            f"\n[{datetime.now().strftime(fmt)[:-2]}] Closed Connection from {file_clients[notified_socket]['data'].decode('utf-8')} On File Socket.")
                        print(f"[{datetime.now().strftime(fmt)[:-2]}] Enter command > ", end="")
                        del file_clients[notified_socket]
                        continue

                if message['data_type'].decode('utf-8') == data_type_msg:
                    user = clients[notified_socket]
                    user_message = format_message(cipher.decrypt(message['data'].decode('utf-8')))
                    print(
                        f"\n[{datetime.now().strftime(fmt)[:-2]}] Received message from {user['data'].decode('utf-8')}: {user_message}")
                    print(f"[{datetime.now().strftime(fmt)[:-2]}] Enter command > ", end="")
                    for client_socket in clients:
                        if client_socket != notified_socket:
                            client_socket.send(
                                user['header'] + user['data'] + message['data_type_header'] + message['data_type'] +
                                message['header'] + message['data'])
                if message['data_type'].decode('utf-8') == data_type_image:
                    user = file_clients[notified_socket]
                    print(
                        f"\n[{datetime.now().strftime(fmt)[:-2]}] Received message from {user['data'].decode('utf-8')}: File of size: {round(len(message['data']) / 1e+6, 3)}MB")
                    print(f"[{datetime.now().strftime(fmt)[:-2]}] Enter command > ", end="")
                    for client_socket in file_clients:
                        if client_socket != notified_socket:
                            client_socket.send(
                                user['header'] + user['data'] + message['data_type_header'] + message['data_type'] +
                                message['extension_header'] + message['extension'] + message['file_header'] + message[
                                    'data'])

        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            del clients[notified_socket]


def BackendInput():
    command = input(f"[{datetime.now().strftime('%d/%m/%Y %H-%M-%S.%f')[:-2]}] Enter command > ")
    return command


def on_join(username, client_socket, join_cipher):
    message = f"{username} Joined the room."
    message = join_cipher.encrypt(message)
    user = {'header': get_header("Server".encode('utf-8')),
            'data': "Server".encode('utf-8')}
    message = {'header': get_header(message),
               'data': message}
    for send_socket in clients:
        if client_socket != send_socket:
            send_socket.send(user['header'] + user['data'] + message['header'] + message['data'])


def kick(username):
    msg = "disconnect"
    msg = cipher.encrypt(msg)
    message_header = get_header(msg)
    message = {'header': message_header, "data": msg}
    server = {'header': get_header("Server".encode('utf-8')),
              'data': "Server".encode('utf-8')}
    data_type = {'header': get_header(data_type_msg.encode('utf-8')), 'data': data_type_msg.encode('utf-8')}
    for client_socket in sockets_list:  # Loop through all the sockets
        if client_socket == server_socket_ssl or client_socket == server_socket_file_ssl:  # If its ours just ignore it
            continue
        else:  # If its not the servers its one of the clients therefore
            user = clients[client_socket]  # Grab the user
            if user['data'].decode('utf-8') == username:  # Compare the usernames
                client_socket.send(server['header'] + server['data'] + data_type['header'] + data_type['data'] + message['header'] + message['data'])
                return True
    return False


def say(msg) -> str:
    code = "[b]"
    code += msg
    msg = code
    msg = format_message(msg)
    msg = cipher.encrypt(msg)
    msg_header = f"{len(msg):<{HEADER_LENGTH}}".encode("utf-8")
    username = "Server".encode('utf-8')
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
    message = {'header': msg_header, 'data': msg}
    data_type = {'header': get_header(data_type_msg.encode('utf-8')), 'data': data_type_msg.encode('utf-8')}
    user = {'header': username_header, 'data': username}
    for client_socket in sockets_list:
        if client_socket == server_socket_ssl or client_socket == server_socket_file_ssl:
            continue
        else:
            try:
                client_socket.send(user['header'] + user['data'] + data_type['header'] + data_type['data'] + message['header'] + message['data'])
            except Exception as e:
                return f"Error: {e}"
    return "True"


def CommandCheck(command, server_thread):
    command_dict = {"/help": "This command will display this view. Syntax: /help",
                    "/close": "This command will kill the server. Syntax: /close",
                    "/stop": "This command will kill the server. Syntax: /stop",
                    "/key": "This command will show the key or iv. Syntax: /key <key or iv>",
                    "/kick": "This command will kick a client from the server. Syntax: /kick <username>",
                    "/connections": "This command will list all of the connected users. Syntax: /connections",
                    "/create": "This command will allow you to create a new user. Syntax: /create <username> <password>",
                    "/remove": "This command will allow you to remove a user. Syntax: /remove <username>",
                    "/users": "This command will list all the current verified users. Syntax: /users"}
    command = command.split(' ')
    new_c, new_connection = login.connect()
    if command[0] == "/help":  # Show commands
        print(f"[{datetime.now().strftime(fmt)[:-2]}] Commands: ")
        for command, reply in command_dict.items():
            print(f"{command}: {reply}")
    elif command[0] == "/close" or command[0] == "/stop":  # Kill the server and all threads
        print("Closing...")
        server_thread.stop()
        raise Exception("Closed from console")
    elif command[0] == "/key":  # Get the key
        if command[1] == "key":
            print(f"[{datetime.now().strftime(fmt)[:-2]}] Key: {key}")
        elif command[1] == "iv":
            print(f"[{datetime.now().strftime(fmt)[:-2]}] IV: {iv}")
        else:
            print("Unrecognised command.")
            CommandCheck("/help", server_thread)
    elif command[0] == "/kick":  # Kick a user from the server
        arg_username = command[1]
        if kick(arg_username):
            print("Success. Wait for the disconnect")
        else:
            print("User not found.")
    elif command[0] == "/connections":  # To list all of the current users connected
        print(f"[{datetime.now().strftime(fmt)[:-2]}] Users: ")
        for user in usernames:
            print(user)
    elif command[0] == "/create":  # This command will allow to create a new user
        username = command[1]
        password = command[2]
        if login.add_user(password.encode('utf-8'), username, 200000, new_c, new_connection):
            print(f"[{datetime.now().strftime(fmt)[:-2]}] Successful. User {username} added.")
        else:
            print(
                f"[{datetime.now().strftime(fmt)[:-2]}] " + login.add_user(password.encode('utf-8'),
                                                                           username, 200000, new_c,
                                                                           new_connection))
    elif command[0] == "/remove":  # This command will remove a user
        username = command[1]
        check = login.remove_user(username, new_c, new_connection)
        if check:
            print(f"[{datetime.now().strftime(fmt)[:-2]}] Successful. User {username} removed.")
        else:
            print(f"[{datetime.now().strftime(fmt)[:-2]}] " + str(check))
    elif command[0] == "/debug":  # This command is a hidden one for devs
        print(clients)
    elif command[0] == "/users":  # Prints list of all current users
        users = login.return_users(new_c)
        print(f"[{datetime.now().strftime(fmt)[:-2]}] Users: ")
        for user in users:
            print(user[0])
    elif command[0] == "/say":
        msg = " ".join(command[1:])
        check = say(msg)
        if check != "True":
            print(check)
        else:
            print("Successful message sent")
    elif "/" not in command[0]:
        msg = " ".join(command)
        check = say(msg)
        if check != "True":
            print(check)
        else:
            print("Successful message sent")
    else:
        print("Unrecognised command")


def start(server_thread):
    while True:
        command = BackendInput()
        if command:
            CommandCheck(command, server_thread)


ServerThread = StoppableThread(target=run, name="ServerThread")
UserInputThread = Thread(target=start, args=(ServerThread,), name="UserInputThread")
ServerThread.setDaemon(True)
ServerThread.start()
UserInputThread.start()
