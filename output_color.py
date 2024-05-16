from termcolor import colored

WHITE = "\x1b[97m"
RED = "\x1b[91m"
GREEN = "\x1b[92m"
YELLOW = "\x1b[93m"
BLUE = "\x1b[94m"
PURPLE = "\x1b[95m"
CYAN = "\x1b[96m"

USE_COLOR = False


def colored_error(err: str) -> str:
    """Red color for error messages

    Args:
        err (str): error message

    Returns:
        str: colored message
    """
    error = colored(err, "red", attrs=['bold'], no_color=USE_COLOR)
    error = error + colored('', 'white')
    return error


def colored_success(mess: str) -> str:
    """Green color for success messages

    Args:
        mess (str): success message

    Returns:
        str: colored message
    """
    message = colored(mess, "light_green", no_color=USE_COLOR)
    message = message + colored('', 'white')
    return message


def colored_info(info: str) -> str:
    """Cyan color for information messages

    Args:
        info (str): information message

    Returns:
        str: colored message
    """
    information = colored(info, 'light_cyan', no_color=USE_COLOR)
    information = information + colored('', 'white')
    return information
