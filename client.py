import os.path
import socket
import time
import json

from base import PORT, DISCONNECT_MESSAGE, ENCODING
from base import recv_header_and_data, send_header_and_data, change_dir, run_shell_command
from scripts.output_color import colored_error, colored_info, colored_success
from scripts.splitter import command_splitter

RETRY_CONNECT_DELAY = 2

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def connect(server_address: tuple) -> None:
    """Connect to a server

    Args:
        server_address (tuple): Address of server to connect with
    """
    retry_count = 1
    while True:
        print(colored_info('\n[Connection to server] ') +
              f'[{server_address[0]}:{server_address[1]}] 📡')
        try:
            client_socket.connect(server_address)
        except (ConnectionRefusedError, TimeoutError):
            print(colored_error('[Connection Error]'))
            retry_count += 1
            print('[Retry to connect] ' + colored_info(f'[{retry_count} retry]') + ' 🔁')
            time.sleep(RETRY_CONNECT_DELAY)
        else:
            print(colored_success('[Connection OK]') + '✅ Connected with server ✅\n')
            break


def send_command(command: str, *args, show_progress=False) -> bytes:
    """Send command with arguments to the server.

    Args:
        command (str): command to send
        *args (tuple, optional): command parameters
        show_progress (bool, optional): Show progressbar if True. Defaults to False.

    Returns:
        bytes: output of command
    """
    final_command = " ".join([command] + list(args))
    send_header_and_data(client_socket, final_command.encode(encoding=ENCODING))
    return recv_header_and_data(client_socket, show_progress=show_progress)


def check_path_type(path: str) -> str:
    """Check if the path on server is directory or file.

    Args:
        path (str): path to check

    Returns:
        str: 'directory' or 'file'
    """
    return send_command('path-type', f'"{path}"').decode(encoding=ENCODING)


def check_path_exists(path: str) -> bool:
    """Check if the path exists on the server.

    Args:
        path (str): path to check

    Returns:
        bool: True if exist else False.
    """
    result = send_command('path-exists', f'"{path}"').decode(encoding=ENCODING)
    return json.loads(result)


def check_path_permission(path: str) -> bool:
    """Check if client has permission to read path on the server.

    Args:
        path (str): path to check

    Returns:
        bool: True if client has permission else False.
    """
    result = send_command('has-permission', f'"{path}"').decode(encoding=ENCODING)
    return json.loads(result)


def list_dir_content(path: str) -> list:
    """List the content of directory on the server

    Args:
        path (str): path of directory

    Returns:
        list: list of all contents
    """
    result = send_command('list-content', f'"{path}"').decode(encoding=ENCODING)
    return json.loads(result)


def download_file(path: str, destination: str) -> None:
    """Download file from server to client machine

    Args:
        path (str): file path on server
        destination (str): client destination path
    """
    print('Downloading ' + colored_info(path))
    output = send_command('download', f'"{path}"', show_progress=True)

    # Write file to the destination
    with open(destination, 'wb') as f:
        f.write(output)

    # Print message that the file has been downloaded successfully
    print('Download ' + colored_info(f'{path}') + ' to ' +
          colored_info(f'{destination}\n'))


def download(path: str, destination: str) -> None:
    """Download file or folder on the server

    Args:
        path (str): path of file or folder
        destination (str): client destination path
    """
    # Check that the given path exists on the server
    if check_path_exists(path):

        if os.path.exists(destination):
            # Check if destination already exist on local machine
            # Ask for new destination if already exists
            print(colored_error(f'[Duplicated file error] Destination "{destination}" already exists.'))
            new_destination = input('New destination: ' + colored_info(': '))
            return download(path, new_destination)

        if check_path_permission(path):
            # check if path on server is directory or file
            path_type = check_path_type(path)

            if path_type == 'file':
                # download the file if path type is file
                download_file(path, destination)

            elif path_type == 'directory':
                # if directory, create folder on local machine, get list of directory content
                # and download each file and directory inside the directory
                os.mkdir(destination)
                os.chdir(destination)
                dir_contents = list_dir_content(path)
                for file in dir_contents:
                    file_path = os.path.join(path, file)
                    download(file_path, file)
                os.chdir('..')

        else:
            print(colored_error(f'[Permission Error] for path "{path}".'))

    else:
        print(colored_error(f"[File Not Found Error] {path} doesn't exists."))


def screenshot(destination: str) -> None:
    """Receive a server screenshot

    Args:
        destination (str): destination path
    """
    output = send_command('capture', show_progress=True)

    if output == 'screenshot-error'.encode(encoding=ENCODING):
        # Error for screenshot command
        print(colored_error("[Screenshot Error]") + "Can't take a screenshot.")

    else:
        # Write the binary file on local machine
        with open(destination, 'wb') as f:
            f.write(output)


def run(server_address: tuple) -> None:
    """Run client socket (run connect(server_ip) before)

    Args:
        server_address (tuple): address of server (ip, port)
    """
    while True:
        try:
            # Get server current working directory and make command prompt with.
            cwd = send_command('info').decode(encoding=ENCODING)
            prompt = ('╭─' + colored_info(f' {server_address[0]}:{server_address[1]}') +
                      f' {cwd}' + '\n╰─' + colored_info(' ❯ '))

            command = ''
            while command == '':
                # Ask for a command to send
                command = input(prompt)

            if command == DISCONNECT_MESSAGE:
                # Disconnect from server if command == 'exit'
                send_header_and_data(client_socket, command.lower().encode(encoding=ENCODING))
                break

            try:
                # Convert command into list of command and arguments
                splitted_command = command_splitter(command)

            except IndexError:
                # For invalid command
                print(colored_error('[Command Error] Your command is invalid.'))

            else:
                if splitted_command[0] == 'local':
                    # Execute local commands
                    # Remove 'local' from command
                    cmd = " ".join(splitted_command[1:])

                    result = ''
                    if command_splitter(cmd)[0] == 'cd':
                        if len(command_splitter(cmd)) == 2:
                            result = change_dir(command_splitter(cmd)[1])
                        else:
                            print(colored_error('[Argument Error]') + 'cd command need one parameter.')
                    else:
                        result = run_shell_command(cmd)

                    print(result)

                elif splitted_command[0] == 'download':
                    if len(splitted_command) == 3:
                        download(splitted_command[-2], splitted_command[-1])
                    elif len(splitted_command) == 2:
                        download(splitted_command[-1], splitted_command[-1])
                    elif len(splitted_command) < 2:
                        print(colored_error('[Parameter Error]') +
                              'download command need one or two arguments.')
                    else:
                        print(colored_error('[Parameter Error]') +
                              'download command accept two arguments maximum.')

                elif splitted_command[0] == 'capture':
                    if len(splitted_command) == 2:
                        screenshot(splitted_command[1])
                    else:
                        print(colored_error('[Parameter Error]') +
                              'capture command need one argument.')

                else:
                    output = send_command(command).decode(encoding=ENCODING)
                    print(output)

        except KeyboardInterrupt:
            continue

    print(colored_success(colored_success(colored_error('You are Disconnected.'))))
    client_socket.close()


if __name__ == '__main__':
    import ipaddress
    while True:
        try:
            server_ip = input(colored_info('[Server IP]: '))
            server_ip = ipaddress.IPv4Address(server_ip)
        except ipaddress.AddressValueError as err:
            print(colored_error('[IP Error]') + ' Invalid IPv4 address.\n' + colored_error(str(err)) + '\n')
        except KeyboardInterrupt:
            break
        else:
            server_addr = (server_ip.exploded, PORT)
            connect(server_addr)
            run(server_addr)
            break
