import socket
import ssl
import sys
from threading import Thread

import select

from encryption import AESCipher

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234
context = ssl.create_default_context()
context.check_hostname = 0
context.verify_mode = 0

my_username = input("Username: ")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

client_socket_ssl = context.wrap_socket(client_socket, do_handshake_on_connect=False)

# Do the SSL handshake this is here due to problems with none blocking __active_sockets
count = 0
while True:
    try:
        count += 1
        client_socket_ssl.do_handshake()
        break
    except ssl.SSLError as err:
        if err.args[0] == ssl.SSL_ERROR_WANT_READ:
            select.select([client_socket_ssl], [], [])
        elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
            select.select([], [client_socket_ssl], [])
        else:
            raise
client_socket_ssl.setblocking(False)


# send username to server SSL encryption
username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket_ssl.send(username_header + username)

# Fetch the AES key from server
key_header = 32
while True:
    try:
        key_header = client_socket_ssl.recv(HEADER_LENGTH)
        break
    except ssl.SSLWantReadError:
        continue
if not len(key_header):
    print("No AES key sent by server. Quitting")
    sys.exit()
key_length = int(key_header.decode('utf-8').strip())
key = client_socket_ssl.recv(key_length)
print(f"Key: {key}")

# Fetch the Initialization Vector from server
iv_header = 16
while True:
    try:
        iv_header = client_socket_ssl.recv(HEADER_LENGTH)
        break
    except ssl.SSLWantReadError:
        continue
if not len(iv_header):
    print("No Initialization vector sent by server. Quitting")
    sys.exit()
iv_length = int(iv_header.decode('utf-8').strip())
iv = client_socket_ssl.recv(iv_length)

# Initialise the AES cipher for encryption and decryption
Cipher = AESCipher(key)
Cipher.setIV(iv)


def MessageInput():
    message = input(f"{my_username} > ")
    return message


def MessageSend(message):
    if message:
        message = Cipher.encrypt(message)
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode("utf-8")
        client_socket_ssl.send(message_header + message)


def MessageReceive():
    while True:
        try:
            # receive things
            username_header = client_socket_ssl.recv(HEADER_LENGTH)
            if not len(username_header):
                print("Connection closed by the server")
                sys.exit()
            username_length = int(username_header.decode('utf-8').strip())
            username = client_socket_ssl.recv(username_length).decode('utf-8')

            message_header = client_socket_ssl.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket_ssl.recv(message_length).decode('utf-8')
            message = Cipher.decrypt(message)
            print(f"\n{username} > {message}\n{my_username} > ", end="")
        except IOError:
            # if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            # print('Reading Error', str(e))
            # sys.exit()
            continue  # Continues if its not those above
            # Only checks to see if the error is one where it is not a "didn't receive anything"
        except Exception as e:
            print('General Error', str(e))
            sys.exit()


def start():
    while True:
        message = MessageInput()
        if message:
            MessageSend(message)


ReceiveThread = Thread(target=MessageReceive)
StartThread = Thread(target=start)
ReceiveThread.setDaemon(True)
ReceiveThread.start()
StartThread.start()
ReceiveThread.join()
StartThread.join()

sys.exit()
