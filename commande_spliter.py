def commande_spliter(cmd: str) -> list:
    quotes_indexs = []
    splited_commande = []
    start_index = 0
    for i in range(len(cmd)):
        if cmd[i] == '"':
            quotes_indexs.append(i)

    if not quotes_indexs:
        splited_commande = cmd.split(' ')

    else:
        i = 0
        while i < len(quotes_indexs):
            splited_commande += cmd[start_index:quotes_indexs[i]].split(' ')
            splited_commande.append(cmd[quotes_indexs[i] + 1:quotes_indexs[i + 1]])
            start_index = quotes_indexs[i + 1] + 1
            i += 2

        n_blank = 0
        for j in splited_commande:
            if j == '':
                n_blank += 1

        for n in range(n_blank):
            splited_commande.remove('')

    return splited_commande
