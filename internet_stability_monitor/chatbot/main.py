"""
Main entry point for the chatbot.

This module initializes and runs the chatbot, connecting all the components.
"""

import sys
import traceback
from typing import Optional, List, Dict, Any, Tuple

# Import from other modules
from internet_stability_monitor.chatbot.memory import ChatbotMemory
from internet_stability_monitor.chatbot.tools import get_tools, set_memory_system
from internet_stability_monitor.chatbot.commands import handle_command, set_dependencies, help_menu_and_list_tools, check_cache
from internet_stability_monitor.chatbot.interface import (
    print_welcome_message, get_user_input, 
    print_ai_thinking, print_ai_message, print_error
)
from internet_stability_monitor.chatbot.agent import ChatbotAgent

# Import for ollama check
import check_ollama_status

def main(silent: bool = False, polite: bool = True):
    """
    Run the chatbot.
    
    Args:
        silent: Whether to run in silent mode (no TTS)
        polite: Whether to run in polite mode (less detailed error messages)
    """
    # Initialize the memory system
    memory = ChatbotMemory()
    
    # Initialize tools and commands
    tools = get_tools()
    set_memory_system(memory)
    
    # Also add command-related tools
    from internet_stability_monitor.chatbot.commands import help_menu_and_list_tools, check_cache, get_local_date_time_and_timezone
    tools.extend([help_menu_and_list_tools, check_cache, get_local_date_time_and_timezone])
    
    # Set dependencies for commands
    set_dependencies(memory, tools)
    
    # Initialize the agent
    agent = ChatbotAgent(tools=tools, memory_system=memory)
    
    # Print welcome message
    print_welcome_message()
    
    # Main loop
    while True:
        if not check_ollama_status.is_ollama_process_running():
            print_error("Ollama process is not running. Please start the Ollama service.")
            check_ollama_status.find_ollama_executable()
            break
        else:
            try:
                # Get user input
                user_input = get_user_input()
                
                # Check for commands
                if handle_command(user_input):
                    continue
                
                # Process user input
                response = agent.process_input(user_input)
                
                # Process the response
                if response and "messages" in response:
                    # Pretty print the last message
                    agent.pretty_print_message(response["messages"][-1])
                
            except KeyboardInterrupt:
                print("\nExiting...")
                memory.save_cache()
                print("Exiting and saving cache...")
                break
            except EOFError:
                print("\nExiting...")
                memory.save_cache()
                print("Exiting and saving cache...")
                break
            except Exception as e:
                print_error(f"An error occurred: {e}")
                traceback.print_exc()

if __name__ == "__main__":
    main()