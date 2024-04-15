import socket
import os
import platform
import subprocess

from tqdm import tqdm

from scripts.output_color import colored_error

if 'windows' in platform.platform().lower():
    os.system('color')

PORT = 4040
HEADER_LEN = 64
MAX_DATA_SIZE = 1048576
ENCODING = 'utf-8'
DISCONNECT_MESSAGE = 'exit'


def send_header_and_data(sock: socket.socket, data: bytes) -> None:
    """Send the length of data then send data

    Args:
        sock (socket.socket): socket that send data
        data (bytes): data to send
    """
    data_header = str(len(data)).zfill(HEADER_LEN)
    sock.sendall(data_header.encode(encoding=ENCODING))
    sock.sendall(data)


def recv_single_data(recv_sock: socket.socket, data_len: int, desc: str = None, show_progress: bool = False) -> bytes:
    """Receive one data from socket

    Args:
        recv_sock (socket.socket): socket that receive data
        data_len (int): data length
        show_progress (bool, optional): If true, show a progress bar when receiving data.
                                        Defaults to False.

    Returns:
        bytes: data received
    """
    desc = "Receiving data" if not desc else desc
    total_data = None
    len_bytes_received = 0
    show_progress = False if data_len < MAX_DATA_SIZE else show_progress

    if show_progress:
        progress = tqdm(range(data_len), desc, unit="B", unit_scale=True,
                        unit_divisor=MAX_DATA_SIZE)

    while len_bytes_received < data_len:
        chunk_len = min(data_len - len_bytes_received, MAX_DATA_SIZE)
        data_part = recv_sock.recv(chunk_len)

        if not data_part:
            return b""
        if not total_data:
            total_data = data_part
        else:
            total_data += data_part

        len_bytes_received += len(data_part)

        if show_progress:
            progress.update(len(data_part))

    return total_data


def recv_header_and_data(recv_sock: socket.socket, desc: str = None, show_progress: bool = False) -> bytes:
    """Receive data header (data length) then data

    Args:
        recv_sock (socket.socket): socket that receive data
        show_progress (bool, optional): If true, show a progress bar when receiving data.
                                        Defaults to False.

    Returns:
        bytes: data received
    """
    header = recv_single_data(recv_sock, HEADER_LEN)
    header = int(header.decode(encoding=ENCODING))
    received_data = recv_single_data(recv_sock, header, desc, show_progress)
    return received_data


def change_dir(directory: str) -> str:
    """Change current directory

    Args:
        directory (str): where to move

    Returns:
        str: the current directory or an error message
    """
    try:
        os.chdir(directory)
    except FileNotFoundError as err:
        return colored_error(str(err))
    except PermissionError as err:
        return colored_error(str(err))

    return os.getcwd()


def run_shell_command(command: str, return_output: bool = True) -> str:
    """Run shell command

    Args:
        command (str): command to run
        return_output (boot): return the output of command if True.

    Returns:
        str: output of command or error
    """
    if return_output:
        output = subprocess.run(command, shell=True, universal_newlines=True,
                                capture_output=True, check=False)
        if output.stdout is None:
            return colored_error('[Error], no output')
        if output.stdout == '':
            return colored_error(output.stderr)

        return output.stdout

    subprocess.run(command, shell=True, universal_newlines=True,
                   capture_output=True, check=False)
