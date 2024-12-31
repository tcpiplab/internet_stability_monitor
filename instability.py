import argparse
import sys
from chat_langchain_ollama_agent import main as chatbot_main
from run_all import main as manual_main
from check_ollama_status import main as check_ollama_status
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
    if script_name == 'all':
        manual_main(silent, polite)
    else:
        print(f"Running script: {script_name}")
        # Here you would add logic to run the specific script by name
        # For example, you might have a dictionary mapping script names to functions
        # scripts = {'script1': script1_function, 'script2': script2_function, ...}
        # scripts[script_name](silent, polite)

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
    parser.add_argument('script_name', nargs='?', default='all', help='Specify the script to run or "all" to run all scripts')
    parser.add_argument('--silent', action='store_true', help='Run in silent mode')
    parser.add_argument('--polite', action='store_true', help='Run in polite mode')
    args = parser.parse_args()

    if args.mode == 'chatbot':
        run_chatbot_mode(args.silent, args.polite)
    elif args.mode == 'manual':
        if args.script_name:
            run_manual_mode(args.script_name, args.silent, args.polite)
        else:
            print("Please specify a script or tool name, or use 'all' to run all scripts.")
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
