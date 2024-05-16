import socket
import time
import subprocess

from base import PORT, DISCONNECT_MESSAGE, ENCODING
from base import recv_header_and_data, send_header_and_data, change_dir
from output_color import colored_error, colored_info, colored_success
from splitter import command_splitter

RETRY_CONNECT_DELAY = 2

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def connect(ip: str) -> None:
    """Connect to a server

    Args:
        ip (str): Server ip address
    """
    retry_count = 1
    while True:
        print('📡 Connect to server ' + colored_info(f'[{ip}:{PORT}]') + ' 📡')
        try:
            client_socket.connect((ip, PORT))
        except ConnectionRefusedError:
            print(colored_error('❌ Connection error ❌'))
            retry_count += 1
            print('🔁 Retry to connect ' + colored_info(f'[{retry_count} retry]') + ' 🔁')
            time.sleep(RETRY_CONNECT_DELAY)
        else:
            print(colored_success('✅ Connected with server ✅'))
            break


def file_already_exist(file_name: str):
    """Check if file exist or not

    Args:
        file_name (str): file name or file path

    Returns:
        str | bool: True | False | "is a directory"
    """
    try:
        file = open(file_name, 'rb')
    except FileNotFoundError:
        return False
    except IsADirectoryError:
        return 'is a directory'

    file.close()
    return True


def download_file(command: str, destination: str) -> None:
    """Download file from server to client machine

    Args:
        command (str): command containing the file path on server and client destination
        destination (str): client destination path
    """
    splitted_command = command_splitter(command)
    error = False

    if destination.lower() == 'q':
        print(colored_error("‼️ File not downloaded."))

    else:
        if file_already_exist(destination) == 'is a directory':
            print(colored_error(f"‼️ {destination} is a directory."))
            error = True

        elif file_already_exist(destination):
            print(colored_error(f'‼️ File {destination} already exists.'))
            error = True

        else:
            # Tell the server to send the file specified in the command
            send_header_and_data(client_socket, command.encode(encoding=ENCODING))

            # Receiving the file or ('file not found' | 'is a directory' | 'screenshot-error')
            output = recv_header_and_data(client_socket, show_progress=True)

            if output == 'file not found'.encode(encoding=ENCODING):
                # The file doesn't exist on the server
                print(colored_error("‼️ File doesn't exists."))

            elif output == 'is a directory'.encode(encoding=ENCODING):
                # The file name specified is a directory
                print(colored_error("‼️ Can't download a directory."))

            elif output == 'screenshot-error'.encode(encoding=ENCODING):
                # Error for screenshot command
                print(colored_error("‼️ Can't take a screenshot."))

            else:
                # The file is received successfully
                # Write the file to the destination
                with open(destination, 'wb') as f:
                    f.write(output)
                print('Download ' + colored_info(f'{splitted_command[1]}') + ' to ' +
                      colored_info(f'{destination}\n'))

        if error:
            new_destination = input('New destination file (or "q" to exit)'
                                    + colored_info(': '))
            download_file(command, new_destination)


def screenshot(command: str, destination: str) -> None:
    """Receive a server screenshot

    Args:
        command (str): command containing the destination path
        destination (str): destination path
    """
    splitted_command = command_splitter(command)
    if len(splitted_command) < 3:
        splitted_command.insert(1, '.screenshot.png')

    new_command = " ".join(splitted_command)
    download_file(new_command, destination)


def run(server_address: tuple) -> None:
    """Run client socket (run connect(server_ip) before)

    Args:
        server_address (tuple): address of server (ip, port)
    """
    while True:
        send_header_and_data(client_socket, 'info'.encode(encoding=ENCODING))
        cwd = recv_header_and_data(client_socket).decode(encoding=ENCODING)
        prompt = ('╭─' + colored_info(f' {server_address[0]}:{server_address[1]}') +
                  f' {cwd}' + '\n╰─' + colored_info(' ❯ '))

        command = ''
        while command == '':
            command = input(prompt)
        if command.lower() == DISCONNECT_MESSAGE:
            send_header_and_data(client_socket, command.lower().encode(encoding=ENCODING))
            break

        try:
            splitted_command = command_splitter(command)
        except IndexError:
            print(colored_error('‼️ Invalid command'))
        else:
            if splitted_command[0] == 'local':
                cmd = " ".join(splitted_command[1:])
                output = subprocess.run(cmd, shell=True, universal_newlines=True,
                                        capture_output=True, check=False)
                if command_splitter(cmd)[0] == 'cd':
                    result = change_dir(command_splitter(cmd)[1])

                else:
                    if output.stdout is None:
                        result = colored_error('❗ Error')
                    elif output.stdout == '':
                        result = colored_error(output.stderr)
                    else:
                        result = output.stdout

                print(result)

            elif len(splitted_command) == 3 and splitted_command[0] == 'download':
                download_file(command, splitted_command[-1])

            elif len(splitted_command) == 2 and splitted_command[0] == 'capture':
                screenshot(command, splitted_command[1])

            else:
                send_header_and_data(client_socket, command.encode(encoding=ENCODING))
                output = recv_header_and_data(client_socket)
                print(output.decode(encoding=ENCODING))

    print(colored_success(colored_success(colored_success('💻 You are Disconnected.'))))
    client_socket.close()


if __name__ == '__main__':
    server_ip = input('💻 Server IP: ')
    connect(server_ip)
    run((server_ip, PORT))
