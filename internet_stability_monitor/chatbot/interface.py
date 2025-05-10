"""
User interface functions for the chatbot.

This module handles the terminal-based UI for the chatbot, including input, output,
and formatting.
"""

import os
import platform
import sys
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
    # Read and print the ASCII header
    try:
        # Use a relative path from the current file to the root of the project
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        header_path = os.path.join(current_dir, 'Instability_ASCII_Header.txt')
        
        with open(header_path, 'r') as f:
            header = f.read()
            print(f"{Fore.GREEN}{header}{Style.RESET_ALL}")
    except Exception as e:
        # Fallback if file can't be read
        print(f"{Fore.GREEN}Welcome to the Internet Stability Monitor Chatbot!{Style.RESET_ALL}")
    
    print(f"Type {Fore.CYAN}/help{Style.RESET_ALL} to see available commands or {Fore.CYAN}/exit{Style.RESET_ALL} to quit.")
    print(f"You can ask questions about your network and internet stability.")
    print(f"I'll explain my thinking process and planning as I help you diagnose issues.")

def get_user_input() -> str:
    """Get input from the user with nice formatting."""
    try:
        return input(f"{Fore.CYAN}\nUser: {Style.RESET_ALL}")
    except EOFError:
        # Handle EOF errors properly
        print("\nDetected EOF, exiting...")
        sys.exit(0)
    except KeyboardInterrupt:
        # Handle Ctrl+C
        print("\nDetected keyboard interrupt, exiting...")
        sys.exit(0)

def print_ai_thinking(message: str):
    """Print an AI thinking message."""
    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Style.DIM}{message}{Style.RESET_ALL}\n")

def print_ai_message(message: str):
    """Print an AI message to the console."""
    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot:{Style.RESET_ALL} {message}")

def print_tool_call(tool_name: str, reason: Optional[str] = None):
    """Print a tool call message with optional reasoning."""
    if reason:
        print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (planning):{Style.RESET_ALL} I'll use {Fore.GREEN}{tool_name}(){Style.RESET_ALL} because {reason}")
    else:
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

def print_planning_step(plan: Dict[str, Any]):
    """Display the agent's planning process."""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}Chatbot (planning):{Style.RESET_ALL}")
    
    # Print reasoning if available
    if "reasoning" in plan:
        print(f"Reasoning: {plan['reasoning']}")
    
    # Print steps
    if "steps" in plan and plan["steps"]:
        print("\nPlanned steps:")
        for i, step in enumerate(plan["steps"], 1):
            print(f"{i}. {step}")
    
    # Print required tools
    if "required_tools" in plan and plan["required_tools"]:
        print("\nTools needed:")
        for tool in plan["required_tools"]:
            print(f"- {tool}")

def print_execution_step(tool: str, result: str):
    """Display a tool execution step."""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}Chatbot (executing):{Style.RESET_ALL} Running {Fore.GREEN}{tool}{Style.RESET_ALL}")
    print(f"Result: {result}")

def print_synthesis(synthesis: str):
    """Display the synthesis of results."""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}Chatbot (synthesizing):{Style.RESET_ALL}")
    print(synthesis)

def format_tool_result(tool_name: str, result: str) -> str:
    """Format a tool result for display."""
    return f"\n{Fore.GREEN}Results from {tool_name}:{Style.RESET_ALL}\n{result}"

def print_conversation_context(context: Dict[str, Any]):
    """Display the current conversation context."""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}Current Context:{Style.RESET_ALL}")
    
    if "cache" in context:
        print("\nCached Information:")
        for key, value in context["cache"].items():
            print(f"- {key}: {value}")
    
    if "recent_tools" in context:
        print("\nRecently Used Tools:")
        for tool in context["recent_tools"]:
            print(f"- {tool['tool']} at {tool['timestamp']}")
    
    if "recent_plans" in context:
        print("\nRecent Plans:")
        for plan in context["recent_plans"]:
            print(f"- Plan from {plan['timestamp']}: {', '.join(plan['plan'].get('steps', []))}")