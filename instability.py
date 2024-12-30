import argparse
import sys
from chat_langchain_ollama_agent import main as chatbot_main
from run_all import main as manual_main
from check_ollama_status import main as check_ollama_status
import importlib.util
from os_utils import OS_TYPE

def check_python_dependencies():
    required_packages = ['requests', 'psutil', 'colorama']
    missing_packages = []

    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing Python packages: {', '.join(missing_packages)}")
        return False
    return True

def run_chatbot_mode(silent, polite):
    # Call the chatbot functionality
    chatbot_main()

def run_manual_mode(silent, polite):
    # Call the manual script execution functionality
    manual_main(silent, polite)

def run_test_mode(silent, polite):
    print("Running in test mode...")
    print(f"Operating System: {OS_TYPE}")
    
    if not check_python_dependencies():
        print("Please install the missing Python packages.")
        return

    if check_ollama_status():
        print("Ollama is running correctly.")
    else:
        print("Ollama is not running. Please check the status.")

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
    parser.add_argument('--silent', action='store_true', help='Run in silent mode')
    parser.add_argument('--polite', action='store_true', help='Run in polite mode')
    args = parser.parse_args()

    if args.mode == 'chatbot':
        run_chatbot_mode(args.silent, args.polite)
    elif args.mode == 'manual':
        run_manual_mode(args.silent, args.polite)
    elif args.mode == 'test':
        run_test_mode(args.silent, args.polite)
    elif args.mode == 'help':
        show_help()
    else:
        print("Invalid mode. Use 'help' for usage information.")
        sys.exit(1)

if __name__ == "__main__":
    main()
