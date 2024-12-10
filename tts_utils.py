from os_utils import OS_TYPE
import subprocess
import os
from colorama import init, Fore, Style

# Colorama will work on macOS, Linux, and on Windows it enables ANSI codes in most common Windows terminals
# Initialize Colorama for autoreset
init(autoreset=True)


def _recommend_espeak_install():
    """
    Print instructions for installing espeak on Linux if it is not yet installed.

    :return: A string with instructions for installing espeak
    """
    # Attempt to detect Linux distribution family from /etc/os-release
    distro_id = None
    distro_like = None

    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("ID="):
                    distro_id = line.strip().split("=")[1].strip('"')
                elif line.startswith("ID_LIKE="):
                    distro_like = line.strip().split("=")[1].strip('"')

    # Determine package manager recommendation based on distro
    # Favor ID_LIKE first, else fallback to ID.
    distro_base = (distro_like or distro_id or "").lower()

    if "debian" in distro_base or "ubuntu" in distro_base:
        return f"Try installing espeak with: {Fore.RED}sudo apt-get install espeak{Style.RESET_ALL}"

    elif "rhel" in distro_base or "centos" in distro_base or "fedora" in distro_base:
        return f"Try installing espeak with: {Fore.RED}sudo yum install espeak{Style.RESET_ALL}"

    else:
        return f"Please install {Fore.RED}espeak{Style.RESET_ALL} using your distribution’s package manager."


def speak_text(tts_text_string: str):
    """
    Use the appropriate TTS command for the current OS.

    - Reads the OS_TYPE variable from os_utils.py
    - If the OS is not supported, print a message and return.
    - If the OS is macOS, use the 'say' command.
    - If the OS is Windows, use the 'powershell' command to use the SAPI.
    - If the OS is Linux, attempt to use 'espeak'. If not available, print instructions for package installation.

    :param tts_text_string: The text to be spoken by the TTS engine
    """

    if OS_TYPE == "macOS":
        subprocess.run(["say", tts_text_string])

    elif OS_TYPE == "Windows":
        subprocess.run([
            "powershell", "-Command",
            "Add-Type -AssemblyName System.Speech; "
            f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{tts_text_string}')"
        ])

    elif OS_TYPE == "Linux":
        # Attempt to run espeak. If unavailable, print instructions.
        try:
            subprocess.run(["espeak", tts_text_string], check=True)

        except FileNotFoundError:
            print(f"{Fore.RED}espeak not found on this Linux system.{Style.RESET_ALL}")
            print(_recommend_espeak_install())

    else:
        print("TTS not supported on this platform.")
