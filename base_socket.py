import socket
import os
import platform
import time
import threading

from tqdm import tqdm

from string_coloring import colored_success, colored_error, colored_info

if 'windows' in platform.platform().lower():
    os.system('color')

ENCODING = 'utf-8'


class BaseSocket:

    MAX_DATA_SIZE = 2048
    HEADER_LEN = 64
    PORT = 5050
    ENCODING = 'utf-8'

    def __init__(self):
        self.clientsocket: socket = None

    def recv_single_data(self, recv_sock: socket, data_len: int, show_progress: bool = False) -> bytes:
        """Reveive single data from another socket

        Args:
            recv_sock (socket): socket that receive data
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
            data_part = recv_sock.recv(chunk_len)

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

    def send_header_and_data(self, sock: socket, data: bytes) -> None:
        """send the header of data followed by the data to the receiver socket

        Args:
            sock (socket): socket that send the data
            data (bytes): data to send
        """
        data_header = str(len(data)).zfill(self.HEADER_LEN)
        sock.sendall(data_header.encode(encoding=ENCODING))
        sock.sendall(data)

    def recv_header_and_data(self, recv_sock: socket, show_progress: bool = False) -> bytes:
        """reveive the header of data followed by the data from sender socket

        Args:
            recv_sock (socket): socket that receive header and data
            show_progress (bool, optional): show data reception progress if True. Defaults to False.

        Returns:
            bytes: data received
        """
        header = self.recv_single_data(recv_sock, self.HEADER_LEN)
        header = int(header.decode(encoding=ENCODING))
        received_datas = self.recv_single_data(recv_sock, header, show_progress)
        return received_datas


class ClientSocket(BaseSocket):

    TIME_DELAY = 3

    def __init__(self):
        super().__init__()
        self.clientsocket: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serveraddress: tuple = (None, None)

    def close_socket(self):
        self.clientsocket.close()

    def connect(self, ip: str) -> None:
        port = super().PORT
        i = 1 
        while True:
            print('📡 Connexion au serveur ' + colored_info(f'{ip}:{port} 📡'))
            try:
                self.clientsocket.connect((ip, port))
            except ConnectionRefusedError:
                print(colored_error('❌ Erreur de connexion! ❌'))
                i += 1
                print(f'🔁 Nouvelle tentative ( {i} ) 🔁')
                time.sleep(self.TIME_DELAY)
            else:
                print(colored_success('\n✅ Connexion etablie avec succes ✅\n'))
                self.serveraddress = ip, port
                break


class ServerSocket(BaseSocket):

    IP = socket.gethostbyname(socket.gethostname())

    def __init__(self):
        super().__init__()
        self.sock: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SOCK_STREAM)
        self.sock.bind((self.IP, self.PORT))
        self.clientaddress = (None, None)

    def close_socket(self):
        self.clientsocket.close()
        self.sock.close()

    def listen(self):
        self.sock.listen()
        print('📡 Attente de connexion sur ' + colored_info(f'{self.IP}:{self.PORT} 📡'))
        self.clientsocket, self.clientaddress = self.sock.accept()
        print(colored_success('✅ Connectee avec ') +
              colored_info(f'{self.clientaddress[0]}:{self.clientaddress[1]} ✅\n'))


class MultipleClientsServerSocket(ServerSocket):

    def __init__(self):
        super().__init__()
        self.clientsockets: dict = {}

    def handle_clients(self, addr: tuple):
        """Handle all client from listen_multiple_clients methode"""
        print(f'💻 {addr} connected 💻')
        print(f'💻 Client(s) connected: {threading.active_count()} 💻')

        connected = True
        while connected:
            client_message = self.recv_header_and_data(self.clientsockets[addr]).decode(self.ENCODING)
            print(f'{addr}: {client_message}')
            if client_message == 'exit':
                break

        self.clientsockets[addr].close()
        del self.clientsockets[addr]

    def linsten_multiple_clients(self):
        self.sock.listen()
        print(f'📡 Attente de connexion sur {self.IP}:{self.PORT} 📡')
        while True:
            clientsocket, clientaddress = self.sock.accept()
            self.clientsockets[clientaddress] = clientsocket
            thread = threading.Thread(target=self.handle_clients(clientaddress))
            thread.start()
