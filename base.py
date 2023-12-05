import socket
import os
import platform
import time

from termcolor import colored
from tqdm import tqdm
from functools import wraps

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


def file_already_exist(file_name):
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
            chunk_len = min(data_len - len_bytes_reveived, self.MAX_DATA_SIZE)
            data_part = self.clientsocket.recv(chunk_len)

            if not data_part:
                return None
            if not all_data:
                all_data = data_part
            else:
                all_data += data_part

            len_bytes_reveived += len(data_part)

            if show_progress:
                progress.update(len(data_part))

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


class ClientSocket(BaseSocket):

    PORT = 4040

    def __init__(self):
        super().__init__()
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serveraddress = (None, None)

    def connect(self, ip: str, port: int = PORT):
        i = 1
        while True:
            print('📡 Connexion au serveur ' + colored_info(f'{ip}:{port} 📡'))
            try:
                self.clientsocket.connect((ip, port))
            except ConnectionRefusedError:
                print(colored_error('❌ Erreur de connexion! ❌'))
                i += 1
                print(f'🔁 Nouvelle tentative ( {i} ) 🔁')
                time.sleep(5)
            else:
                print(colored_success('\n✅ Connexion etablie avec succes ✅\n'))
                self.serveraddress = ip, port
                self.connected = True
                break


class ServerSocket(BaseSocket):

    PORT = 4040
    IP = socket.gethostbyname(socket.gethostname())

    def __init__(self, ip: str = IP, port: int = PORT):
        super().__init__()
        self.sock: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.clientaddress = (None, None)

    def listen(self):
        self.sock.listen()
        print('📡 Attente de connexion sur ' + colored_info(f'{self.IP}:{self.PORT} 📡'))
        self.clientsocket, self.clientaddress = self.sock.accept()
        print(colored_success('✅ Connectee avec ') +
              colored_info(f'{self.clientaddress[0]}:{self.clientaddress[1]} ✅\n'))
        self.connected = True
