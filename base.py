import socket
from termcolor import colored
from tqdm import tqdm
from functools import wraps
import os
import platform

if 'windows' in platform.platform().lower():
    os.system('color')

use_color = False

ENCODING = 'utf-8'
# Couleurs pour le terminal
WHITE = "\x1b[97m"
RED = "\x1b[91m"
GREEN = "\x1b[92m"
YELLOW = "\x1b[93m"
BLUE = "\x1b[94m"
PURPLE = "\x1b[95m"
CYAN = "\x1b[96m"


def colored_error(err: str) -> str:
    error = colored(err, "red", attrs=['bold'], no_color=use_color)
    return error


def colored_success(mess: str) -> str:
    message = colored(mess, "light_green", no_color=use_color)
    return message


def colored_info(info: str) -> str:
    information = colored(info, 'light_cyan', no_color=use_color)
    return information


def already_exist(file_name):
    try:
        file = open(file_name, 'r')
    except FileNotFoundError:
        return False
    except IsADirectoryError:
        return 'isdir'
    else:
        file.close()
        return True


class BaseSocket:

    MAX_DATA_SIZE = 1024

    def __init__(self):
        self.connected = False
        self.clientsocket: socket = None

    @staticmethod
    def is_connected(method):
        @wraps(method)
        def _impl(self, *method_args, **method_kwargs):
            if self.connected:
                return method(self, *method_args, **method_kwargs)
            else:
                print(colored_error(f'‼️ Socket non connecte.'))

        return _impl

    @is_connected
    def recv_single_data(self, data_len: int, show_progress: bool = False):
        """Reveive data from another socket

        Args:
            data_len (int): data to be received length
            show_progress (bool, optional): show data reception progress. Defaults to False.

        Returns:
            bytes: data reveived
        """
        all_data = None
        len_bytes_reveived = 0

        if show_progress:
            progress = tqdm(range(data_len), colored_success(f"Receiving data"), unit="B", unit_scale=True,
                            unit_divisor=self.MAX_DATA_SIZE)

        while len_bytes_reveived < data_len:
            chunk = min(data_len - len_bytes_reveived, self.MAX_DATA_SIZE)
            data = self.clientsocket.recv(chunk)

            if not data:
                return None
            if not all_data:
                all_data = data
            else:
                all_data += data

            len_bytes_reveived += len(data)

            if show_progress:
                progress.update(len(data))

        return all_data

    @is_connected
    def send_header_data(self, data):
        """send data after his header to the receiver socket

        Args:
            data (bytes): data to send
        """
        cmd_header = str(len(data)).zfill(13)
        self.clientsocket.sendall(cmd_header.encode(encoding=ENCODING))
        self.clientsocket.sendall(data)

    @is_connected
    def recv_header_data(self, show_progress: bool = False):
        """reveive data after his header from sender socket

        Args:
            show_progress (bool, optional): show data reception progress. Defaults to False.

        Returns:
            bytes: data received after sending data
        """
        header = self.recv_single_data(13)
        header = int(header.decode(encoding=ENCODING))
        received_datas = self.recv_single_data(header, show_progress)
        return received_datas
