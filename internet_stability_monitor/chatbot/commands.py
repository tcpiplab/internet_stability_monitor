"""
Command handlers for the chatbot.

This module defines the command handlers for commands like /help, /exit, etc.
"""

from typing import Dict, Any, Callable, List, Optional
import datetime
from colorama import Fore, Style
from langchain_core.tools import tool

# These will be set by the main module
memory_system = None
all_tools = []

def set_dependencies(memory, tools):
    """Set the dependencies for the commands module."""
    global memory_system, all_tools
    memory_system = memory
    all_tools = tools

def get_first_line(desc):
    """Get the first line of a description safely."""
    if not desc:
        return ""
    lines = desc.split('\n')
    return lines[0] if lines else ""

@tool
def help_menu_and_list_tools() -> None:
    """Use this when the user inputs 'help' to guide them with a list the available tools and their descriptions.

    Output: Prints a list of available tools and their descriptions.

    Returns: None
    """
    tools_list = "\n".join([f"- {Fore.GREEN}{tool_object.name}{Style.RESET_ALL}: {get_first_line(tool_object.description)}" 
                          for tool_object in all_tools])

    help_text = f"""
{Fore.CYAN}Available chat commands:{Style.RESET_ALL}
- {Fore.GREEN}/help{Style.RESET_ALL}: Show this help message
- {Fore.GREEN}/exit{Style.RESET_ALL}: Exit the chatbot
- {Fore.GREEN}/clear{Style.RESET_ALL}: Clear conversation history
- {Fore.GREEN}/history{Style.RESET_ALL}: Show recent conversation history
- {Fore.GREEN}/memory{Style.RESET_ALL}: Show detailed conversation state
- {Fore.GREEN}/tools{Style.RESET_ALL}: List all available tools
- {Fore.GREEN}/cache{Style.RESET_ALL}: Show cached data
- {Fore.GREEN}/tool_history{Style.RESET_ALL}: Show recently used tools

{Fore.CYAN}Available tools:{Style.RESET_ALL}
{tools_list}

End of help menu.
"""

    print(help_text)
    return None

@tool
def check_cache() -> str:
    """Use this to check the cache (memories) and print the keys and values from the cache file.

    Returns: str: The cache contents
    """
    try:
        if memory_system:
            cache = memory_system.cache
            if memory_system:
                memory_system.record_tool_call("check_cache", {}, f"Cached Data Context: {cache}")
            return f"Cached Data Context: {cache}"
        else:
            return "Error: Memory system not initialized."
    except Exception as e:
        print(f"{Fore.RED}Error loading cache: {e}{Style.RESET_ALL}")
        return "Error loading cache."

@tool
def get_local_date_time_and_timezone() -> List[str]:
    """Use this to get the local date, time, and timezone.

    Returns: list: the local time in 24-hour format, the local date in the format YYYY-MM-DD, and the local timezone
    """
    # Return the local time in 24-hour format
    local_time = datetime.datetime.now().strftime("%H:%M")

    # Return the local date in the format YYYY-MM-DD
    local_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Return the local timezone
    local_timezone = datetime.datetime.now().astimezone().tzinfo

    result = [local_time, local_date, str(local_timezone)]
    if memory_system:
        memory_system.record_tool_call("get_local_date_time_and_timezone", {}, result)
    return result

def display_help():
    """Display the help menu without using the LangChain tool."""
    tools_list = "\n".join([f"- {Fore.GREEN}{tool_object.name}{Style.RESET_ALL}: {get_first_line(tool_object.description)}" 
                          for tool_object in all_tools])

    help_text = f"""
{Fore.CYAN}Available chat commands:{Style.RESET_ALL}
- {Fore.GREEN}/help{Style.RESET_ALL}: Show this help message
- {Fore.GREEN}/exit{Style.RESET_ALL}: Exit the chatbot
- {Fore.GREEN}/clear{Style.RESET_ALL}: Clear conversation history
- {Fore.GREEN}/history{Style.RESET_ALL}: Show recent conversation history
- {Fore.GREEN}/memory{Style.RESET_ALL}: Show detailed conversation state
- {Fore.GREEN}/tools{Style.RESET_ALL}: List all available tools
- {Fore.GREEN}/cache{Style.RESET_ALL}: Show cached data
- {Fore.GREEN}/tool_history{Style.RESET_ALL}: Show recently used tools

{Fore.CYAN}Available tools:{Style.RESET_ALL}
{tools_list}

End of help menu.
"""
    print(help_text)

def handle_command(command: str, graph = None) -> bool:
    """Handle a command and return True if the command was handled."""
    if command.lower() in ["/exit", "/quit"]:
        print("\nExiting...")
        if memory_system:
            memory_system.save_cache()
        print("Exiting and saving cache...")
        return True
    
    elif command.lower() in ["/help", "help", "/?", "?"]:
        display_help()
        return True

    elif command.lower() == "/clear":
        if memory_system:
            memory_system.clear_history()
        print(f"{Fore.GREEN}Conversation history cleared.{Style.RESET_ALL}")
        return True
    
    elif command.lower() == "/history":
        if memory_system:
            history = memory_system.format_history_output()
            print(f"{Fore.YELLOW}Conversation History:{Style.RESET_ALL}\n{history}")
        else:
            print(f"{Fore.RED}Memory system not initialized.{Style.RESET_ALL}")
        return True
    
    elif command.lower() == "/memory":
        try:
            print(f"{Fore.YELLOW}Memory contents:{Style.RESET_ALL}")
            
            if memory_system and hasattr(memory_system, "memory"):
                config = memory_system.get_config()
                checkpoint_data = memory_system.memory.get_tuple(config)
                
                if checkpoint_data:
                    print(f"CheckpointTuple found with {len(checkpoint_data) if hasattr(checkpoint_data, '__len__') else 'unknown'} elements")
                    
                    # Get more information about tuple elements
                    if hasattr(checkpoint_data, "_fields"):
                        print(f"Named fields: {checkpoint_data._fields}")
                    
                    # Try to extract the stored messages
                    for i, elem in enumerate(checkpoint_data):
                        if isinstance(elem, list):
                            print(f"\nElement {i} is a list with {len(elem)} items")
                            if len(elem) > 0:
                                print(f"First item type: {type(elem[0])}")
                                # If we found potential messages, show a few
                                for j, item in enumerate(elem[:3]):
                                    content = getattr(item, "content", str(item)[:50])
                                    item_type = getattr(item, "type", type(item).__name__)
                                    print(f"  Item {j}: {item_type} - {content[:50]}...")
                        
                        elif isinstance(elem, dict):
                            print(f"\nElement {i} is a dict with keys: {elem.keys()}")
                            if "messages" in elem:
                                print(f"Found 'messages' in element {i} with {len(elem['messages'])} items")
                                if len(elem["messages"]) > 0:
                                    # Display a few sample messages
                                    for j, msg in enumerate(elem["messages"][-3:]):
                                        content = getattr(msg, "content", str(msg)[:50])
                                        msg_type = getattr(msg, "type", type(msg).__name__)
                                        print(f"  Message {j}: {msg_type} - {content[:50]}...")
                else:
                    print("No checkpoint data found")
            else:
                print(f"{Fore.RED}Memory or memory system not initialized.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error accessing memory: {e}{Style.RESET_ALL}")
            import traceback
            print(f"{Fore.YELLOW}Traceback: {traceback.format_exc()}{Style.RESET_ALL}")
        return True
    
    elif command.lower() == "/tools":
        # Display a list of available tools
        tools_list = "\n".join([f"- {Fore.GREEN}{tool_object.name}{Style.RESET_ALL}: {get_first_line(tool_object.description)}" 
                            for tool_object in all_tools])
        print(f"{Fore.YELLOW}Available tools:{Style.RESET_ALL}\n{tools_list}")
        return True
    
    elif command.lower() == "/cache":
        print(f"{Fore.YELLOW}Cache (memories): {memory_system.cache if memory_system else 'Memory system not initialized'}{Style.RESET_ALL}")
        return True
    
    elif command.lower() == "/tool_history":
        if memory_system:
            tool_history = memory_system.get_tool_history()
            if tool_history:
                print(f"{Fore.YELLOW}Tool History (most recent calls first):{Style.RESET_ALL}")
                for i, call in enumerate(reversed(tool_history)):
                    print(f"{i+1}. {Fore.GREEN}{call['tool']}{Style.RESET_ALL} ({call['timestamp']})")
                    if call.get('args'):
                        args_str = ", ".join(f"{k}={v}" for k, v in call['args'].items())
                        print(f"   Args: {args_str}")
                    print(f"   Result: {call['result_summary']}")
            else:
                print(f"{Fore.YELLOW}No tool history found.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Memory system not initialized.{Style.RESET_ALL}")
        return True
    
    return False