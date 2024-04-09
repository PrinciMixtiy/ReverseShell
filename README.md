# Backdoor

Backdoor project implemented with python and socket.

*Target*: server.py
*Hacker*: client.py

![Project screenshot](assets/images/backdoor.png)

## Python Requirements

- pillow
- termcolor
- tqdm

```shell
python -m pip install pillow termcolor tqdm
```

## Initialization

### 1- Run the server

Run `server.py` on the target machine.  
The target machine must be on the same local network and can be the same machine where clients run.

```shell
[IP List] List of IP address

1 - ('127.0.0.1', 4040)

In which address would you like to run the server?
[IP Choice]: 
```

Chose the your IP address where server will running and press Enter.

```shell
python server.py

[Server start] at [127.0.0.1:4040] 📡
```

### 2- Run client

Run `client.py` and enter the IP address of the server.

```shell
python client.py

[Server IP]: 
```

```shell
[Server IP]: 127.0.0.1
```

```shell
[Connection to server] [192.168.56.1:4040] 📡
[Connection OK]✅ Connected with server ✅
╭─ 127.0.0.1:4040 /Backdoor
╰─ ❯ 
```

### 3- Send command to the server

```shell
╭─ 127.0.0.1:4040 /Backdoor
╰─ ❯ ls
```

## Specials commands

### 1- Download file or folder on the server

```shell
download <filename or foldername> <destination>
```

### 2- Take screenshot of server

```shell
capture <destination.png>
# Don't forget .png file extension.
```

### 3- Give information about server OS

```shell
os
```

### 4- List all clients connected with the server

```shell
clients
```

### 5- Run local command

```shell
local <command>
```

### Disconnect to the server

```shell
exit
```

## Notes

- Use double quote (not single quote) when passing an argument containing space.  

    ```shell
    download "file name.txt" file.txt
    ```
