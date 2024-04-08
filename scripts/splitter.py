def command_splitter(cmd: str) -> list:
    """Convert a command from user input to list of command and arguments

    Args:
        cmd (str): command from user input

    Returns:
        list: command splitted
    """
    quotes_indexes = []
    splitted_command = []
    start_index = 0

    for i, _ in enumerate(cmd):
        if cmd[i] == '"':
            quotes_indexes.append(i)

    if not quotes_indexes:
        splitted_command = cmd.split(' ')

    else:
        for i in range(0, len(quotes_indexes), 2):
            splitted_command += cmd[start_index:quotes_indexes[i]].split(' ')
            splitted_command.append(cmd[quotes_indexes[i] + 1:quotes_indexes[i + 1]])
            start_index = quotes_indexes[i + 1] + 1

        splitted_command += cmd[quotes_indexes[-1]+1:].split(' ')

        n_blank = 0
        for j in splitted_command:
            if j == '':
                n_blank += 1

        for _ in range(n_blank):
            splitted_command.remove('')

    return splitted_command
