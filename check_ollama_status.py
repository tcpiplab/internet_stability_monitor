# check_local_ollama.py
import requests
import psutil
import shutil
import os


def is_ollama_api_reachable():
    try:
        response = requests.get(
            "http://localhost:11434/api/generate")  # Adjust the endpoint according to the actual status endpoint
        return response.status_code
    except requests.ConnectionError as e:
        print(f"Connection error: {e}")
        return False


def is_ollama_process_running():
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if "ollama" in proc.info['name']:
            return True
    return False


def find_ollama_executable():
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
        print("To manually start the Ollama service, run the following command:")
        print(f"{ollama_path} serve")
        return False

    elif ollama_path is None:
        print("Ollama executable not found. Please ensure it is installed and in your PATH.")
        return False


def main():
    if not is_ollama_api_reachable():
        print("The local Ollama API is not reachable.")

        if not is_ollama_process_running():
            print("The local Ollama process is not running.")
            find_ollama_executable()
            return False

        else:
            print("The local Ollama process is already running. But you may need to check its configuration.")
            return False
    else:
        print("The local Ollama API is reachable.")
        return True


if __name__ == "__main__":
    main()
