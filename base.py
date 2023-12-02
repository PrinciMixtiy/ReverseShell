import socket


# Couleurs pour le terminal
WHITE = "\x1b[97m"
RED = "\x1b[91m"
GREEN = "\x1b[92m"
YELLOW = "\x1b[93m"
BLUE = "\x1b[94m"
PURPLE = "\x1b[95m"
CYAN = "\x1b[96m"


class BaseSocket:

    MAX_DATA_SIZE = 1024

    def __init__(self):
        self.connected = False
        self.clientsocket: socket = None

    def is_connected(self, f):
        """decorator checking if the communication socket is connected"""
        def wrapper(*args, **kwargs):
            if self.connected:
                return f(*args, **kwargs)
            else:
                print(f'{RED}‼️ Socket non connecte.{WHITE}')
        return wrapper()

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
                print(f"Donnees recues: {len_bytes_reveived}/{data_len} | "
                      f"{CYAN}{round(len_bytes_reveived / data_len * 100, 2)}%")

        return all_data

    def send_header_data(self, data):
        """send data after his header to the receiver socket

        Args:
            data (bytes): data to send
        """
        cmd_header = str(len(data)).zfill(13)
        self.clientsocket.sendall(cmd_header.encode())
        self.clientsocket.sendall(data)

    def recv_header_data(self, show_progress: bool = False):
        """reveive data after his header from sender socket

        Args:
            show_progress (bool, optional): show data reception progress. Defaults to False.

        Returns:
            bytes: data received after sending data
        """
        header = self.recv_single_data(13)
        header = int(header.decode())
        received_datas = self.recv_single_data(header, show_progress)
        return received_datas
