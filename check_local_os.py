import platform
import subprocess


def get_os_type():
    os_type = platform.system()
    if os_type == "Darwin":
        return "macOS"
    elif os_type == "Windows":
        return "Windows"
    elif os_type == "Linux":
        return "Linux"
    else:
        return "Unknown"


if __name__ == "__main__":
    os_type = get_os_type()
    print(f"The internet infrastructure monitoring scripts are running on : {os_type}")
    subprocess.run(["say", f"The internet infrastructure monitoring scripts are running on : {os_type}"])