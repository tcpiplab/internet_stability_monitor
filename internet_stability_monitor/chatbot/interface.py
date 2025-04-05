"""
User interface functions for the chatbot.

This module handles the terminal-based UI for the chatbot, including input, output,
and formatting.
"""

import platform
from typing import Dict, Any, Callable, List, Optional
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Import readline for input history and completion 
if platform.system() == "Windows":
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None
else:
    try:
        import readline
    except ImportError:
        readline = None

# Set up readline if available
if readline and platform.system() != "Windows":
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")

def print_welcome_message():
    """Print a welcome message to the user."""
    print(f"{Fore.GREEN}Welcome to the Internet Stability Monitor Chatbot!{Style.RESET_ALL}")
    print(f"Type {Fore.CYAN}/help{Style.RESET_ALL} to see available commands or {Fore.CYAN}/exit{Style.RESET_ALL} to quit.")
    print(f"You can ask questions about your network and internet stability.")

def get_user_input() -> str:
    """Get input from the user with nice formatting."""
    return input(f"{Fore.CYAN}\nUser: {Style.RESET_ALL}")

def print_ai_thinking(message: str):
    """Print an AI thinking message."""
    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {message}")

def print_ai_message(message: str):
    """Print an AI message to the console."""
    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot:{Style.RESET_ALL} {message}")

def print_tool_call(tool_name: str):
    """Print a tool call message."""
    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (calling tool):{Style.RESET_ALL} {Fore.GREEN}{tool_name}(){Style.RESET_ALL}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"{Fore.YELLOW}Warning: {message}{Style.RESET_ALL}")

def print_debug(message: str):
    """Print a debug message."""
    print(f"{Fore.MAGENTA}Debug: {message}{Style.RESET_ALL}")

def print_success(message: str):
    """Print a success message."""
    print(f"{Fore.GREEN}Success: {message}{Style.RESET_ALL}")