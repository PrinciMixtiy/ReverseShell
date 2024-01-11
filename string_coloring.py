from termcolor import colored

# Couleurs pour le terminal
WHITE = "\x1b[97m"
RED = "\x1b[91m"
GREEN = "\x1b[92m"
YELLOW = "\x1b[93m"
BLUE = "\x1b[94m"
PURPLE = "\x1b[95m"
CYAN = "\x1b[96m"

use_color = False


def colored_error(err: str) -> str:
    error = colored(err, "red", attrs=['bold'], no_color=use_color)
    return error


def colored_success(mess: str) -> str:
    message = colored(mess, "light_green", no_color=use_color)
    return message


def colored_info(info: str) -> str:
    information = colored(info, 'light_cyan', no_color=use_color)
    return information
