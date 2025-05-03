"""
Main entry point for the chatbot.

This module handles the main chat loop and command processing.
"""

import sys
from typing import Optional

from .agent import ChatbotAgent
from .memory import ChatbotMemory
from .commands import handle_command, set_dependencies
from .interface import (
    print_welcome_message,
    get_user_input,
    print_ai_message,
    print_error
)
from .tool_providers import get_default_providers

def main(cache_file: Optional[str] = None) -> None:
    """Run the main chatbot loop.
    
    Args:
        cache_file: Optional path to the cache file
    """
    try:
        # Initialize memory
        memory = ChatbotMemory(cache_file)
        
        # Initialize the agent with default tool providers
        agent = ChatbotAgent(
            tool_providers=get_default_providers(),
            memory_system=memory
        )
        
        # Set up command dependencies
        set_dependencies(memory, agent.tools)
        
        # Print welcome message
        print_welcome_message()
        
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = get_user_input()
                
                # Check for exit command
                if user_input.lower() in ["/exit", "/quit"]:
                    break
                    
                # Handle commands
                if user_input.startswith("/"):
                    handle_command(user_input, memory)
                    continue
                
                # Process through agent
                result = agent.process_input(user_input)
                
                # Print the agent's final response
                if result and 'response' in result:
                    # Use the interface function for consistent AI output formatting
                    print_ai_message(result['response'])
                    
                    # Optionally, print intermediate steps for debugging/user info
                    # if 'intermediate_steps' in result and result['intermediate_steps']:
                    #    print("\n--- Intermediate Steps ---")
                    #    for step in result['intermediate_steps']:
                    #        print(step)
                    #    print("------------------------\n")
                else:
                    # Handle cases where agent might not return a response (e.g., error during processing)
                    print_error("Chatbot did not provide a response.")
                    
            except KeyboardInterrupt:
                print("\nUse /exit to quit")
            except Exception as e:
                print_error(f"Error processing input: {e}")
                
    except KeyboardInterrupt:
        print("\nSaving cache and exiting...")
    except Exception as e:
        print_error(f"Fatal error: {e}")
    finally:
        # Save cache before exiting
        if memory:
            memory.save_cache()

if __name__ == "__main__":
    main()