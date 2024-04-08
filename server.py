import socket
import threading
import platform
import os
import json

from PIL import ImageGrab

from base import PORT, ENCODING, DISCONNECT_MESSAGE
from base import change_dir, send_header_and_data, recv_header_and_data, run_shell_command

from scripts.output_color import colored_error, colored_info, colored_success
from scripts.splitter import command_splitter


def handle_clients(clients: dict, addr: tuple) -> None:
    """Handle each client connected to the server

    Args:
        clients (dict): dictionary of all clients connected to the server
                        {client_address: client_socket,}
        addr (tuple): address of client
    """
    print(colored_success('[New connection]: ') +
          f'[{addr[0]}:{addr[1]}] connected.' +
          colored_info(f'[{threading.active_count() - 1}  Clients 💻]')
          )

    while True:
        command = recv_header_and_data(recv_sock=clients[addr]).decode(encoding=ENCODING)
        splitted_command = command_splitter(command)
        result = ''

        if (not command) or (command == DISCONNECT_MESSAGE):
            # Disconnect the client.
            break

        # --------------- Those are not directly used by clients ------------------

        if command == 'info':
            # Send current working directory
            result = os.getcwd()

        # --------------- Commands to run before download -------------------------
        elif splitted_command[0] == 'path-exists':
            # Send True if path exists else False. (serialized with json)
            result = json.dumps(os.path.exists(" ".join(splitted_command[1:])))

        elif splitted_command[0] == 'has-permission':
            # Send True if has permission to read on path else False. (serialized with json)
            result = json.dumps(os.access(splitted_command[1], mode=os.R_OK))

        elif splitted_command[0] == 'path-type':
            # Send path type. ('directory' or 'file')
            if os.path.isdir(splitted_command[-1]):
                result = 'directory'
            elif os.path.isfile(splitted_command[-1]):
                result = 'file'

        elif splitted_command[0] == 'list-content':
            # Send list of directory contents. (serialized with json)
            result = json.dumps(os.listdir(" ".join(splitted_command[1:])))
        # -------------------------------------------------------------------------

        # -------------------------------------------------------------------------

        # --------------- Commands used by clients --------------------------------

        elif splitted_command[0] == 'cd':
            # Change directory.
            if len(splitted_command) == 2:
                result = change_dir(splitted_command[1])
            else:
                result = colored_error('[Argument Error] for cd command.')

        elif command == 'os':
            # Send Information about OS.
            result = platform.platform()

        elif command == 'clients':
            # Send list of clients connected to the server.
            client_list = []
            for num, address in enumerate(clients.keys()):
                client_list.append(f'[Client {num+1}]: [{address[0]}:{address[1]}]')
            result = json.dumps(client_list)

        elif splitted_command[0] == 'download':
            # Send file or directory to the client.
            path = splitted_command[-1]
            with open(path, 'rb') as f:
                result = f.read()

        elif splitted_command[0] == 'capture':
            # Take and send screenshot.
            try:
                image = ImageGrab.grab()
                image.save('.screenshot.png', 'png')
                with open('.screenshot.png', 'rb') as img:
                    result = img.read()
                os.remove('.screenshot.png')
            except OSError:
                result = 'screenshot-error'
        # -------------------------------------------------------------------------

        # --------------- Shell Commands ------------------------------------------
        else:
            result = run_shell_command(command)
        # -------------------------------------------------------------------------

        if splitted_command[0] not in \
                ['info', 'path-exists', 'has-permission', 'path-type', 'list-content']:
            print(colored_info(f'[{addr[0]}:{addr[1]}] ⌨ >') + f' {command}')

        if not result:
            result = colored_error('[Error], no output')

        if isinstance(result, str):
            result = result.encode(encoding=ENCODING)

        send_header_and_data(clients[addr], result)

    print(colored_success(f'[{addr[0]}: {addr[1]}] Disconnected 👋'))
    del clients[addr]


def start_server(addr: tuple, sock: socket.socket) -> None:
    """Start the server and listen for clients connections
    """
    clients = {}

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SOCK_STREAM)
    sock.bind(addr)
    sock.listen()

    print(colored_success('\n[Server start]') + ' at ' + colored_info(f'[{addr[0]}:{addr[1]}]') + ' 📡')

    while True:
        try:
            client_socket, client_address = sock.accept()
        except KeyboardInterrupt:
            confirm = input('\nDo you want to stop the server? [y/n]: ')
            if 'y' in confirm.lower():
                break
            else:
                continue
        else:
            clients[client_address] = client_socket
            thread = threading.Thread(target=handle_clients, args=(clients, client_address,))
            thread.start()

    sock.close()
    print(colored_error('[Server down] 👻👋'))


if __name__ == '__main__':
    while True:
        ip_list = socket.getaddrinfo(socket.gethostname(), PORT, family=socket.AF_INET)
        print(colored_info('[IP List]') + ' List of IP address\n')
        for i, ip in enumerate(ip_list):
            print(colored_info(f'{i+1}') + f' - {ip[-1]}')

        print('\nIn which address would you like to run the server?')

        try:
            server_index = int(input(colored_info('[IP Choice]: ')))
            server_address = ip_list[server_index-1][-1]
        except (ValueError, IndexError):
            print(colored_error('\n[Choice Error] ' + f'Chose between {[i+1 for i in range(len(ip_list))]}'))
        except KeyboardInterrupt:
            print(colored_error('Exit'))
            break
        else:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            start_server(server_address, server_socket)
            break
