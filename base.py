import socket
import time
import asyncio

from tqdm import tqdm

MAX_DATA_SIZE = 2048
HEADER_LEN = 64
PORT = 5050
ENCODING = 'UTF-8'


async def send_header_and_data(sock: socket, data: bytes) -> None:
    data_header = str(len(data)).zfill(HEADER_LEN)
    sock.sendall(data_header.encode(encoding=ENCODING))
    sock.sendall(data)


async def recv_single_data(recv_sock: socket, data_len: int, show_progress: bool = False) -> bytes:
    all_data = None
    len_bytes_reveived = 0

    if show_progress:
        progress = tqdm(range(data_len), "Receiving data", unit="B", unit_scale=True,
                        unit_divisor=MAX_DATA_SIZE)

    while len_bytes_reveived < data_len:
        chunk_len = min(data_len - len_bytes_reveived, MAX_DATA_SIZE)
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


async def recv_header_and_data(recv_sock: socket, show_progress: bool = False) -> bytes:
    header = await recv_single_data(recv_sock, HEADER_LEN)
    header = int(header.decode(encoding=ENCODING))
    received_datas = await recv_single_data(recv_sock, header, show_progress)
    return received_datas


class ClientSocket:

    RETRY_CONNECT_DELAY = 2

    def __init__(self):
        self.clientsocket: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serveraddress: tuple = (None, None)

    def connect(self, ip: str) -> None:
        port = PORT
        i = 1
        while True:
            print(f'📡 Connexion au serveur {ip}: {port} 📡')
            try:
                self.clientsocket.connect((ip, port))
            except ConnectionRefusedError:
                print('❌ Erreur de connexion! ❌')
                i += 1
                print(f'🔁 Nouvelle tentative ({i}) 🔁')
                time.sleep(self.RETRY_CONNECT_DELAY)
            else:
                print('\n✅ Connexion etablie avec succes ✅\n')
                self.serveraddress = ip, port
                break


class ServerSocket:

    def __init__(self):
        self.IP = socket.gethostbyname(socket.gethostname())
        self.sock: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SOCK_STREAM)
        self.sock.bind((self.IP, PORT))
        self.clientsockets: dict = {}

    async def listen(self):
        self.sock.listen()
        print(f'📡 Attente de connexion sur {self.IP}: {PORT} 📡')
        while True:
            clientsocket, clientaddress = self.sock.accept()
            self.clientsockets[clientaddress] = clientsocket
            await asyncio.create_task(self.handle_clients(clientaddress))

    async def handle_clients(self, addr: tuple):
        print(f'💻 {addr} connected 💻')

        connected = True
        while connected:
            client_message = await recv_header_and_data(self.clientsockets[addr])
            client_message = client_message.decode(ENCODING)
            await asyncio.sleep(1)
            print(f'{addr}: {client_message}')
            if client_message == 'exit':
                break

        self.clientsockets[addr].close()
        del self.clientsockets[addr]
