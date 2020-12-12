import socket
import ssl
import os

from encryption import AESCipher
from threading import Thread

HEADER_LENGTH = 10
data_type_msg = "msg"
data_type_image = "image"
try:
    os.mkdir("app/")
    os.mkdir("app/downloads/")
    os.mkdir("app/temp/")
except FileExistsError:
    pass


def get_header(data):
    header = f"{len(data):<{HEADER_LENGTH}}".encode("utf-8")
    return header


# noinspection PyShadowingNames,PyBroadException
def receive_message(client_socket, error_callback):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False
        message_length = int(message_header.decode("utf-8").strip())
        return {'header': message_header, "data": client_socket.recv(message_length)}
    except socket.timeout:
        error_callback("Timed out.")
    except:
        return False


# noinspection PyUnboundLocalVariable
def connect(my_username, my_password, ip, port, error_callback):
    IP = ip
    PORT = port
    context = ssl.create_default_context()
    context.check_hostname = 0
    context.verify_mode = 0

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client_socket_ssl = context.wrap_socket(client_socket)
        client_socket_ssl.connect((IP, PORT))
        client_socket_ssl.settimeout(5)
    except Exception as e:
        error_callback("Connection Error: {}".format(str(e)))
        return False

    # send username to server SSL encryption
    username = my_username.encode('utf-8')
    UnEncryptedMessageSend(username, client_socket_ssl)

    password = my_password.encode('utf-8')
    UnEncryptedMessageSend(password, client_socket_ssl)

    # Fetch the AES key from server
    key_data = receive_message(client_socket_ssl, error_callback)
    if not key_data:
        error_callback("No AES key sent. Is it the correct Username/Password?")
        return False
    key = key_data['data']

    client_socket_ssl.send(key)  # Send the key for checking

    msg_data = receive_message(client_socket_ssl, error_callback)
    msg = msg_data['data'].decode('utf-8')
    if msg != "Fine":  # Checks to see if the message was an error
        error_callback(f"{msg}")

    iv_data = receive_message(client_socket_ssl, error_callback)
    iv = iv_data['data']

    client_socket_ssl.send(iv)  # Send the IV for the handshake
    msg_data = receive_message(client_socket_ssl, error_callback)
    msg = msg_data['data'].decode('utf-8')
    if msg != "Fine":  # Checks to see if the message was an error
        error_callback(f"{msg}")

    # Initialise the AES cipher for encryption and decryption
    Cipher = AESCipher(key)
    Cipher.setIV(iv)
    client_socket_ssl.setblocking(False)

    try:
        client_socket_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client_socket_file_ssl = context.wrap_socket(client_socket_file)
        client_socket_file_ssl.connect((IP, (PORT + 1)))
    except Exception as e:
        error_callback("Connection Error: {}".format(str(e)))
        return False

    # send username to server SSL encryption
    UnEncryptedMessageSend(username, client_socket_file_ssl)

    return client_socket_ssl, Cipher, username.decode('utf-8'), client_socket_file_ssl


def EncryptedMessageSend(message, cipher, client_socket_ssl):
    data_type = data_type_msg.encode('utf-8')
    data_type_header = get_header(data_type)
    if message:
        message = cipher.encrypt(message)
        message_header = get_header(message)
        client_socket_ssl.send(data_type_header + data_type + message_header + message)


def UnEncryptedMessageSend(message, client_socket_ssl):
    data_type = data_type_msg.encode('utf-8')
    data_type_header = get_header(data_type)
    if message:
        message_header = get_header(message)
        client_socket_ssl.send(data_type_header + data_type + message_header + message)


def ImageDecode(cipher, message_callback, username, file_bytes, extension):
    count = 0
    with open("app/temp/download.enc", "wb") as f:
        f.write(file_bytes)
    file_exists = True
    while file_exists:
        print(os.path.exists(f"app/downloads/Download{count}{extension}"))
        if os.path.exists(f"app/downloads/Download{count}{extension}"):
            count += 1
        else:
            file_exists = False
    path = f"Download{count}{extension}"
    cipher.decrypt_file(in_filename="app/temp/download.enc", out_filename=f"app/downloads/{path}")
    message_callback(username, f"File received saved at app/downloads/{path}.")


def SendImage(path, cipher, client_socket_ssl, message_callback):
    allowed_files = [".png", ".jpg", ".jpeg"]
    if (os.path.getsize(path) / 1e+6) > 8:
        message_callback("System", "File size too large please keep to 8MB or lower")
    else:
        filepath, file_extension = os.path.splitext(path)
        if file_extension in allowed_files:
            file_extension_header = get_header(file_extension.encode('utf-8'))
            cipher.encrypt_file(path, out_filename=f"app/temp/{os.path.splitext(os.path.basename(path))[0]}.enc")
            encrypted_file = "app/temp/" + os.path.splitext(os.path.basename(path))[0] + ".enc"
            with open(encrypted_file, "rb") as f:
                image_bytes = f.read()
            image_header = get_header(image_bytes)
            try:
                client_socket_ssl.send(get_header(data_type_image.encode('utf-8')) + data_type_image.encode('utf-8') + file_extension_header
                                       + file_extension.encode('utf-8') + image_header + image_bytes)
            except ssl.SSLWantWriteError:
                pass
        else:
            message_callback("System", f"File type not allowed only, {str(allowed_files)}")
    return True


def ImageMessageReceive(file_socket, cipher, error_callback, message_callback, speed):
    while True:
        try:
            username_header = file_socket.recv(HEADER_LENGTH)
            if not len(username_header):
                error_callback("Connection closed by the server")
            username_length = int(username_header.decode('utf-8').strip())
            username = file_socket.recv(username_length).decode('utf-8')

            data_type_header = file_socket.recv(HEADER_LENGTH)
            if not len(data_type_header):
                error_callback("Connection closed by the server")
            data_type_length = int(data_type_header.decode('utf-8').strip())
            data_type = file_socket.recv(data_type_length).decode('utf-8')

            if data_type == data_type_image:
                extension_header = file_socket.recv(HEADER_LENGTH)
                print(extension_header)
                extension_length = int(extension_header.decode('utf-8').strip())
                extension = file_socket.recv(extension_length).decode('utf-8')

                file_header = file_socket.recv(HEADER_LENGTH)
                file_length = int(file_header.decode('utf-8').strip())
                file_bytes = b""
                while len(file_bytes) != file_length:
                    file_bytes += file_socket.recv(speed)
                ImageDecode(cipher, message_callback, username, file_bytes, extension)

        except Exception as e:
            error_callback(f'General Error {str(e)}')


def MessageReceive(client_socket_ssl, cipher, error_callback, message_callback):
    while True:
        try:
            # receive things
            username_header = client_socket_ssl.recv(HEADER_LENGTH)
            if not len(username_header):
                error_callback("Connection closed by the server")
            username_length = int(username_header.decode('utf-8').strip())
            username = client_socket_ssl.recv(username_length).decode('utf-8')

            data_type_header = client_socket_ssl.recv(HEADER_LENGTH)
            if not len(data_type_header):
                error_callback("Connection closed by the server")
            data_type_length = int(data_type_header.decode('utf-8').strip())
            data_type = client_socket_ssl.recv(data_type_length).decode('utf-8')

            if data_type == data_type_msg:
                message_header = client_socket_ssl.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                message = client_socket_ssl.recv(message_length).decode('utf-8')
                message = cipher.decrypt(message)
                if message == "disconnect" and username == "Server":
                    error_callback("Kicked from Server.")
                message_callback(username, message)
            elif data_type == data_type_image:
                extension_header = client_socket_ssl.recv(HEADER_LENGTH)
                print(extension_header)
                extension_length = int(extension_header.decode('utf-8').strip())
                extension = client_socket_ssl.recv(extension_length).decode('utf-8')

                file_header = client_socket_ssl.recv(HEADER_LENGTH)
                file_length = int(file_header.decode('utf-8').strip())
                file_bytes = client_socket_ssl.recv(file_length)
                ImageDecode(cipher, message_callback, username, file_bytes, extension)
        except ssl.SSLWantReadError:
            continue  # Continues if its not those above (That error is waiting for a didn't receive)
            # Only checks to see if the error is one where it is not a "didn't receive anything"
        except BlockingIOError:
            continue
        except Exception as e:
            error_callback(f'General Error {str(e)}')


def disconnect(client_socket: socket):
    client_socket.close()


# noinspection PyShadowingNames
def start(socket, cipher, error_callback, incoming_message_callback, file_socket, speed):
    ReceiveThread = Thread(target=MessageReceive, args=(socket, cipher, error_callback, incoming_message_callback))
    ImageReceiveThread = Thread(target=ImageMessageReceive, args=(file_socket, cipher, error_callback, incoming_message_callback, speed))
    ReceiveThread.setDaemon(True)
    ImageReceiveThread.setDaemon(True)
    ReceiveThread.start()
    ImageReceiveThread.start()

# def start(my_username, cipher, client_socket_ssl):
#    while True:
#        message = MessageInput(my_username)
#        if message:
#            MessageSend(message, cipher, client_socket_ssl)
