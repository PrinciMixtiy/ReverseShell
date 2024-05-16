# backdoor

Backdoor project with python and sockets

## Python Requirements

- termcolor
- tqdm
- pillow

## Initialization

- run **server.py** on the target machine (can be the same machine where **client.py** is running)
- run **client.py**
- Enter the IP address of the server (the target)
- Press Enter (Server and client have been connected)
- You can send **shell commands** and receive outputs from the server

## Specials commands

- **download** {filename(required)} {destination(required)}
- **capture** {destination(required)}
- **os**
- **clients**
- **local** {command(required)}
- **exit**
