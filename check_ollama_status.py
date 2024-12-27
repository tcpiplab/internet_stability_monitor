# check_local_ollama.py
import requests
import psutil
import shutil
import os
from colorama import init, Fore, Style

# Initialize the colorama module with autoreset=True
init(autoreset=True)


def is_ollama_api_reachable():
    """
    This function will check if the Ollama API is reachable on your system.

    Inputs: None

    Returns: str: HTTP status code if the Ollama API is reachable, False if it is not.
    """

    try:

        response = requests.get(
            "http://localhost:11434/api/generate")  # Adjust the endpoint according to the actual Ollama endpoint

        return response.status_code

    except requests.ConnectionError as e:

        print(f"Connection error: {e}")

        return False


def is_ollama_process_running():
    """This function will check if the Ollama process is running on your system.

    Inputs: None

    Returns: bool: True if the Ollama process is running, False if it is not.
    """
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if "ollama" in proc.info['name']:
            return True
    return False


def find_ollama_executable():
    """This function will attempt to find the path to the ollama executable on your system, regardless of OS or CPU type.

    Inputs: None

    Returns: bool: False if the ollama executable is not found, True if it is found.
    """

    ollama_path = shutil.which("ollama")
    # This will output the exact path to the ollama executable currently in use.
    # If it returns no output, the ollama command may not be installed properly or isn’t in your PATH.
    # If you installed it via Homebrew, the path is likely /opt/homebrew/bin/ollama on ARM-based Macs
    # or /usr/local/bin/ollama on Intel-based Macs.
    # If you installed it via pip, the path is likely ~/.local/bin/ollama
    # If you installed it via conda, the path is likely ~/miniconda3/bin/ollama.
    # If you installed it via Docker, the path is likely /usr/local/bin/ollama.
    #
    # Now check each of those paths to see if the ollama executable exists and, if so, save its path in the ollama_path variable.

    possible_ollama_paths = [
        "/opt/homebrew/bin/ollama",  # For ARM-based Macs
        "/usr/local/bin/ollama",     # For Intel-based Macs
        "~/.local/bin/ollama",       # For Homebrew users
        "~/miniconda3/bin/ollama",   # For conda users
        "/usr/local/bin/ollama"      # For Docker users
    ]

    for path in possible_ollama_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            ollama_path = expanded_path
            break

    if ollama_path is not None:
        print(f"{Fore.RED}To manually start the Ollama service, run the following command in a separate terminal, then return here and try again:\n{Style.RESET_ALL}")
        print(f"\t{Fore.GREEN}{ollama_path} serve\n{Style.RESET_ALL}")
        return False

    elif ollama_path is None:
        print(f"{Fore.RED}Ollama executable not found. Please ensure it is installed and in your {Style.BRIGHT}PATH{Style.NORMAL}.{Style.RESET_ALL}")
        return False


def main():
    if not is_ollama_api_reachable():
        print(f"{Fore.RED}The local Ollama API is not reachable.{Style.RESET_ALL}")

        if not is_ollama_process_running():
            print(f"{Fore.RED}The local Ollama process is not running.{Style.RESET_ALL}")
            find_ollama_executable()
            return False

        else:
            print(f"{Fore.RED}The local Ollama process is already running. But you may need to check its configuration.{Style.RESET_ALL}")
            return False
    else:
        print(f"{Fore.GREEN}The local Ollama API is reachable.{Style.RESET_ALL}")
        return True


if __name__ == "__main__":
    main()
