import argparse
import sys
from chat_langchain_ollama_agent import main as chatbot_main
from run_all import main as manual_main
from check_ollama_status import main as check_ollama_status
from cdn_check import main as cdn_check_main
from check_external_ip import main as check_external_ip_main
from cloud_check import main as cloud_check_main
from dns_check import main as dns_check_main
from imap_check import main as imap_check_main
from ixp_check import main as ixp_check_main
from mac_speed_test import main as mac_speed_test_main
from ntp_check import main as ntp_check_main
from resolver_check import main as resolver_check_main
from smtp_check import main as smtp_check_main
from tls_ca_check import main as tls_ca_check_main
from web_check import main as web_check_main
from whois_check import main as whois_check_main
import importlib.util
from colorama import init, Fore
from os_utils import OS_TYPE

# Initialize colorama
init(autoreset=True)

def check_python_dependencies():
    missing_packages = []

    with open('requirements.txt', 'r') as file:
        for line in file:
            package = line.split('==')[0].split('~')[0].strip()
            # Map known package names to their import equivalents
            package_map = {
                'langchain_ollama': 'langchain-ollama',
                'dnspython': 'dns',
                'python-whois': 'whois',
            }
            import_name = package_map.get(package, package)
            if importlib.util.find_spec(import_name) is None:
                missing_packages.append(package)

    if missing_packages:
        print(f"Missing Python packages: {', '.join(missing_packages)}. Please run the following command to install them:")
        print("python -m pip install -r requirements.txt")
        return False
    return True

def run_chatbot_mode(silent, polite):
    # Call the chatbot functionality
    chatbot_main()

def run_manual_mode(script_name, silent, polite):
    scripts = {
        "check_external_ip": check_external_ip_main,
        "mac_speed_test": mac_speed_test_main,
        "resolver_check": resolver_check_main,
        "whois_check": whois_check_main,
        "dns_check": dns_check_main,
        "ntp_check": ntp_check_main,
        "web_check": web_check_main,
        "cloud_check": cloud_check_main,
        "imap_check": imap_check_main,
        "smtp_check": smtp_check_main,
        "tls_ca_check": tls_ca_check_main,
        "cdn_check": cdn_check_main,
        "ixp_check": ixp_check_main
    }
    
    if script_name == 'all':
        manual_main(silent, polite)
    elif script_name in scripts:
        print(f"Running script: {script_name}")
        scripts[script_name](silent, polite)
    else:
        print(f"Script '{script_name}' not found. Please specify a valid script name.")

def run_test_mode(silent, polite):
    print(f"{Fore.YELLOW}Running in test mode...{Fore.RESET}")
    print(f"{Fore.YELLOW}Operating System: {OS_TYPE}{Fore.RESET}")
    
    try:
        if check_ollama_status():
            print(f"{Fore.GREEN}Ollama is running correctly.{Fore.RESET}")
        else:
            print(f"{Fore.RED}Ollama is not running. Please check the status.{Fore.RESET}")
    except ModuleNotFoundError as e:
        print(f"{Fore.RED}Error: {e}{Fore.RESET}")
        print("It seems like some required packages are missing.")
        print("Please ensure you are using a virtual environment and that it is activated.")
        print("Run the following command to install all required packages:")
        print("python -m pip install -r requirements.txt")

def show_help():
    # Display help information
    print("Usage: instability.py <mode> [options]")
    print("Modes:")
    print("  chatbot  - Run the interactive chatbot")
    print("  manual   - Run all scripts manually")
    print("  test     - Run tests")
    print("  help     - Show this help message")
    print("Options:")
    print("  --silent - Run in silent mode")
    print("  --polite - Run in polite mode")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('mode', choices=['chatbot', 'manual', 'test', 'help'], help='Mode of operation')
    parser.add_argument('script_name', nargs='?', help='Specify the script to run or "all" to run all scripts')
    parser.add_argument('--silent', action='store_true', help='Run in silent mode')
    parser.add_argument('--polite', action='store_true', help='Run in polite mode')
    args = parser.parse_args()

    if args.mode == 'chatbot':
        run_chatbot_mode(args.silent, args.polite)
    elif args.mode == 'manual':
        if args.script_name:
            run_manual_mode(args.script_name, args.silent, args.polite)
        else:
            available_scripts = [
                "check_external_ip",
                "mac_speed_test",
                "resolver_check",
                "whois_check",
                "dns_check",
                "ntp_check",
                "web_check",
                "cloud_check",
                "imap_check",
                "smtp_check",
                "tls_ca_check",
                "cdn_check",
                "ixp_check"
            ]
            print("Please specify a script or tool name, or use 'all' to run all scripts.")
            print("Available scripts:")
            for script in available_scripts:
                print(f"- {script}")
            sys.exit(1)
    elif args.mode == 'test':
        run_test_mode(args.silent, args.polite)
    elif args.mode == 'help':
        show_help()
    else:
        print("Invalid mode. Use 'help' for usage information.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except ModuleNotFoundError as e:
        print(f"{Fore.RED}Error: {e}{Fore.RESET}")
        print("It seems like some required packages are missing.")
        print("Please activate the correct virtual environment and run the following command:")
        print("python -m pip install -r requirements.txt")
