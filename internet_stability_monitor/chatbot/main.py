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
from internet_stability_monitor.chatbot.commands import handle_command, set_dependencies
from internet_stability_monitor.chatbot.interface import (
    print_welcome_message, get_user_input, 
    print_ai_thinking, print_ai_message, print_error,
    print_planning_step, print_execution_step, print_synthesis
)
from internet_stability_monitor.chatbot.agent import EnhancedChatbotAgent
from internet_stability_monitor.chatbot.planning import PlanningSystem

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
    
    # Also add command-related tools that should be available to the model
    from internet_stability_monitor.chatbot.commands import help_menu_and_list_tools, check_cache, get_local_date_time_and_timezone
    # Make these tools available to the model but handle them separately in UI when needed
    tools.extend([check_cache, get_local_date_time_and_timezone])
    
    # Set dependencies for commands
    set_dependencies(memory, tools)
    
    # Initialize the planning system
    planner = PlanningSystem()
    
    # Initialize the enhanced agent
    agent = EnhancedChatbotAgent(tools=tools, memory_system=memory)
    
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
                handled, should_exit = handle_command(user_input)
                if handled:
                    if should_exit:
                        break  # Exit the loop if the command indicates we should exit
                    else:
                        continue
                
                # Process user input
                print_ai_thinking("Planning approach...")
                response = agent.process_input(user_input)
                
                # Process the response
                if response:
                    # Show planning if available
                    if "plan" in response:
                        print_planning_step(response["plan"])
                    
                    # Show execution steps if available
                    if "results" in response:
                        for result in response["results"]:
                            print_execution_step(result["tool"], result["result"])
                    
                    # Show final response
                    if "messages" in response:
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