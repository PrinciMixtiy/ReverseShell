import socket
import os
import platform
import time

from tqdm import tqdm
from functools import wraps

from string_coloring import colored_success, colored_error, colored_info

if 'windows' in platform.platform().lower():
    os.system('color')

ENCODING = 'utf-8'


class BaseSocket:

    MAX_DATA_SIZE = 2048
    HEADER_LEN = 64

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
    def recv_single_data(self, data_len: int, show_progress: bool = False) -> bytes:
        """Reveive single data from another socket

        Args:
            data_len (int): length of data to be received length
            show_progress (bool, optional): show data reception progress if True. Defaults to False.

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
                return b""
            if not all_data:
                all_data = data_part
            else:
                all_data += data_part

            len_bytes_reveived += len(data_part)

            if show_progress:
                progress.update(len(data_part))

        return all_data

    @is_connected
    def send_header_and_data(self, data: bytes) -> None:
        """send the header of data followed by the data to the receiver socket

        Args:
            data (bytes): data to send
        """
        data_header = str(len(data)).zfill(self.HEADER_LEN)
        self.clientsocket.sendall(data_header.encode(encoding=ENCODING))
        self.clientsocket.sendall(data)

    @is_connected
    def recv_header_and_data(self, show_progress: bool = False) -> bytes:
        """reveive the header of data followed by the data from sender socket

        Args:
            show_progress (bool, optional): show data reception progress if True. Defaults to False.

        Returns:
            bytes: data received
        """
        header = self.recv_single_data(self.HEADER_LEN)
        header = int(header.decode(encoding=ENCODING))
        received_datas = self.recv_single_data(header, show_progress)
        return received_datas


class ClientSocket(BaseSocket):

    PORT = 4040

    def __init__(self):
        super().__init__()
        self.clientsocket: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serveraddress: tuple = (None, None)

    def connect(self, ip: str, port: int = PORT) -> None:
        i = 1
        while True:
            print('📡 Connexion au serveur ' + colored_info(f'{ip}:{port} 📡'))
            try:
                self.clientsocket.connect((ip, port))
            except ConnectionRefusedError:
                print(colored_error('❌ Erreur de connexion! ❌'))
                i += 1
                print(f'🔁 Nouvelle tentative ( {i} ) 🔁')
                time.sleep(3)
            else:
                print(colored_success('\n✅ Connexion etablie avec succes ✅\n'))
                self.serveraddress = ip, port
                self.connected = True
                break


class ServerSocket(BaseSocket):

    PORT = 4040
    IP = socket.gethostbyname(socket.gethostname())

    def __init__(self):
        super().__init__()
        self.sock: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SOCK_STREAM)
        self.sock.bind((self.IP, self.PORT))
        self.clientaddress = (None, None)

    def listen(self):
        self.sock.listen()
        print('📡 Attente de connexion sur ' + colored_info(f'{self.IP}:{self.PORT} 📡'))
        self.clientsocket, self.clientaddress = self.sock.accept()
        print(colored_success('✅ Connectee avec ') +
              colored_info(f'{self.clientaddress[0]}:{self.clientaddress[1]} ✅\n'))
        self.connected = True
