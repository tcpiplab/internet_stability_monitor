import platform
import subprocess
import argparse

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


def main(silent):
    os_type = get_os_type()
    print(f"The internet infrastructure monitoring scripts are running on : {os_type}")
    if not silent:
        subprocess.run(["say", f"The internet infrastructure monitoring scripts are running on {os_type}"])

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Internet Infrastructure Monitoring Script")
    parser.add_argument("--silent", action="store_true", help="Run in silent mode with no voice output")
    args = parser.parse_args()

    main(args.silent)
