from typing import Optional, List, Dict, Any, Tuple, Literal
import datetime
import platform
from chatbot_cache_persister import load_cache, save_cache, update_cache, get_cached_value

# Import readline for input history and completion
if platform.system() == "Windows":
    import pyreadline3 as readline
else:
    import readline

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from os_utils import get_os_type
from report_source_location import get_public_ip, get_isp_and_location
from check_if_external_ip_changed import did_external_ip_change
from cdn_check import main as cdn_check_main
from tls_ca_check import main as tls_ca_check_main
from whois_check import main as whois_check_main
import socket
import check_ollama_status
from resolver_check import monitor_dns_resolvers
from dns_check import check_dns_root_servers, dns_root_servers
from dns_check import main as check_all_root_servers
from check_layer_two_network import report_link_status_and_type
from os_utils import OS_TYPE
from web_check import main as web_check_main
import subprocess
from colorama import init, Fore, Style
import mac_speed_test
from smtp_check import main as smtp_check_main
# Major refactor of the code to use the new in-memory checkpointer
# https://langchain-ai.github.io/langgraph/tutorials/introduction/#part-3-adding-memory-to-the-chatbot
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated
# from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition










# Initialize the colorama module with autoreset=True
init(autoreset=True)

# Set up readline to store input history
if platform.system() != "Windows":
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")


@tool
def check_smtp_servers() -> str:
    """Use this to check the reachability of several important SMTP servers.

    Returns: str: The SMTP server monitoring report
    """
    return smtp_check_main(silent=True, polite=False)


@tool
def run_mac_speed_test() -> str:
    """Use this to run the mac speed test and get a summary of the network quality.

    Returns: str: The mac speed test report or an error message if not on macOS
    """
    if OS_TYPE.lower() != "macOS".lower():
        return "The mac speed test is only available on macOS."
    return mac_speed_test.run_network_quality_test(silent=True, args=None)


@tool
def check_ollama():
    """Use this to check if the Ollama process is running and/or if the Ollama API is reachable."""
    return check_ollama_status.main()

@tool
def check_cdn_reachability() -> str:
    """Use this to check the reachability of several of the largest content delivery networks around the world.

    Returns: str: The CDN reachability report
    """
    return cdn_check_main(silent=True, polite=False)

@tool
def ping_target(target: str) -> str:
    """Use this to ping an IP address or hostname to determine the network latency.

    Args:
        target (str): The IP address or hostname to ping.

    Returns: str: The average latency in milliseconds, or an error message if the ping fails.
    """
    try:
        # Run the ping command
        result = subprocess.run(
            ["ping", "-c", "4", target],
            capture_output=True,
            text=True,
            check=True
        )
        # Extract the average latency from the ping output
        for line in result.stdout.splitlines():
            if "avg" in line:
                return line.split("/")[4] + " ms"
        return "Ping completed, but average latency could not be determined."
    except subprocess.CalledProcessError as e:
        return f"Ping failed: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

@tool
def check_whois_servers() -> str:
    """Use this to check the reachability of WHOIS servers.

    Returns: str: The WHOIS server monitoring report
    """
    return whois_check_main(silent=True, polite=False)

@tool
def check_tls_ca_servers() -> str:
    """Use this to check the reachability of TLS CA servers.

    Returns: str: The TLS CA server monitoring report
    """
    return tls_ca_check_main(silent=True, polite=False)

@tool
def get_os() -> str:
    """Use this to get os information.

    Returns: str: the os type
    """
    return get_os_type()

@tool
def get_local_ip() -> str:
    """Use this to get our local IP address that we're using for the local LAN, Ethernet, or WiFi network.

    Returns: str: this computer's local ip address
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

@tool
def get_external_ip() -> str:
    """Use this to get our external ip address.

    Returns: str: our external ip address
    """
    our_external_ip = get_public_ip()
    return our_external_ip

@tool
def check_external_ip_change() -> str:
    """Use this to check if the external IP address has changed since the last check.

    Returns: str: A message indicating whether the IP address has changed or not.
    """
    # Get the current external IP using the existing tool
    current_external_ip = get_public_ip()

    # Check if the external IP has changed
    external_ip_status_message = did_external_ip_change(current_external_ip)

    return external_ip_status_message


@tool
def get_isp_location() -> dict[str, Any]:
    """
    Use this to get our external ISP location data based on our external IP address.
    Uses the ipinfo.io API to get the ISP name and location data.

    Returns: str: JSON formatted ISP name and location data
    """
    our_external_ip = get_public_ip()
    our_isp_json = get_isp_and_location(our_external_ip)

    return our_isp_json

@tool
def check_internet_connection() -> str:
    """Use this to check if we have a working internet broadband connection, including basic DNS lookup of www.google.com.

    Returns: str: "connected" if we have an internet connection, "disconnected" if we don't
    """
    try:
        socket.create_connection(("www.google.com", 80))
        return "connected"
    except OSError:
        return "disconnected"

@tool
def check_layer_three_network() -> str:
    """Use this to check if we have a working layer 3 internet broadband connection and can reach 8.8.8.8 on port 53.

    Returns: str: "connected at layer 3" if we have an internet connection, "disconnected at layer 3" if we don't
    """
    try:
        socket.create_connection(("8.8.8.8", 53))
        return "connected at layer 3"
    except OSError:
        return "disconnected at layer 3"

@tool
def check_dns_resolvers() -> str:
    """Use this to check the reachability of several of the most popular DNS resolvers.

    Returns: str: the DNS resolver monitoring report
    """
    return monitor_dns_resolvers()


@tool
def check_websites() -> str:
    """Use this to check the reachability of several important websites.

    Returns: str: The website monitoring report
    """
    return web_check_main(silent=True, polite=False)


@tool
def check_dns_root_servers_reachability() -> str:
    """Use this to check the reachability of the major DNS Root Servers around the world.

    Returns: str: the DNS root server monitoring report
    """

    # # The mandatory argument dns_root_servers is defined in dns_check.py
    # return check_dns_root_servers(dns_root_servers)

    return check_all_root_servers(silent=True, polite=False)


@tool
def check_local_layer_two_network() -> str:
    """Use this to check the local LAN OSI Layer 2 network link type, speed, and status.
        For example, it will print the LAN network interfaces that are up,
        and if they are up and have a speed greater than 0 Mbps, it will also print the link type and speed.
        It will also try to guess if the network interface is Wi-Fi, Ethernet, Loopback, or Unknown.

    Returns: str: for interfaces that are up, the link name, type guess, and speed
    """
    return report_link_status_and_type()

@tool
def help_menu_and_list_tools() -> None:
    """Use this when the user inputs 'help' to guide them with a list the available tools and their descriptions.

    Output: Prints a list of available tools and their descriptions.

    Returns: None
    """
    # Tools will be defined later, but we'll use them in the actual function
    # We use a safe method to extract first line of description without backslashes
    def get_first_line(desc):
        if not desc:
            return ""
        lines = desc.split('\n')
        return lines[0] if lines else ""
    
    # Get the list of tools at runtime, not definition time
    tools_list = "\n".join([f"- {Fore.GREEN}{tool_object.name}{Style.RESET_ALL}: {get_first_line(tool_object.description)}" 
                           for tool_object in tools])

    help_text = f"""
{Fore.CYAN}Available chat commands:{Style.RESET_ALL}
- {Fore.GREEN}/help{Style.RESET_ALL}: Show this help message
- {Fore.GREEN}/exit{Style.RESET_ALL}: Exit the chatbot
- {Fore.GREEN}/clear{Style.RESET_ALL}: Clear conversation history
- {Fore.GREEN}/history{Style.RESET_ALL}: Show recent conversation history
- {Fore.GREEN}/tools{Style.RESET_ALL}: List all available tools
- {Fore.GREEN}/cache{Style.RESET_ALL}: Show cached data

{Fore.CYAN}Available tools:{Style.RESET_ALL}
{tools_list}

End of help menu.
"""

    print(help_text)

    return None


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

    return [local_time, local_date, local_timezone]

@tool
def check_cache() -> str:
    """Use this to check the cache (memories) and print the keys and values from the cache file.

    Returns: str: The cache contents
    """

    try:

        # Load the cache
        cache = load_cache()

    except Exception as e:
        print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.RED}Error loading cache: {e}{Style.RESET_ALL}")
        return "Error loading cache."

    # Print a message to indicate that the cache has been loaded
    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (thinking):{Style.RESET_ALL} {Fore.GREEN}Cache (memories) loaded successfully.{Style.RESET_ALL}")

    return f"Cached Data Context: {cache}"


# New memory system code below

search_tool = TavilySearchResults(max_results=2)



# Initialize the memory saver, an in-memory checkpointer to replace the clumsy cache system we have now
memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)


# Define the tools
tools = [
    check_ollama,
    get_os,
    get_local_ip,
    check_internet_connection,
    check_layer_three_network,
    get_external_ip,
    check_external_ip_change,
    get_isp_location,
    check_dns_resolvers,
    check_websites,
    check_dns_root_servers_reachability,
    check_local_layer_two_network,
    help_menu_and_list_tools,
    get_local_date_time_and_timezone,
    ping_target,
    check_tls_ca_servers,
    check_whois_servers,
    check_cdn_reachability,
    run_mac_speed_test,
    check_smtp_servers,
    check_cache,
    search_tool
]




model = ChatOllama(model="qwen2.5").bind_tools(tools)


def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}


# Define the system prompt
system_prompt = ("You are a precise network diagnostics assistant. Follow these guidelines for tool usage:"
                 "\n1. IMPORTANT: When a user request closely matches a specific tool's purpose, use ONLY that tool"
                 "\n2. For example, if a user asks to 'check websites' or 'check significant websites', use ONLY the check_websites tool"
                 "\n3. Use multiple tools ONLY when necessary to fulfill distinct parts of a complex request"
                 "\n4. Avoid using the search tool unless explicitly requested or when local tools cannot answer the question"
                 "\n5. Prioritize direct tool names over general descriptions (e.g., 'check_dns_resolvers' over general DNS queries)"
                 "\n6. If a tool's response is verbose, summarize only the most important troubleshooting information"
                 "\nYour primary job is network diagnostics using available tools, not general information retrieval.")



graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

# compile the graph with the provided checkpointer
graph = graph_builder.compile(checkpointer=memory)

# Flag to track if this is the first message in the conversation
_first_message = True

# Function to check and update the first_message flag
def _is_first_message():
    global _first_message
    if _first_message:
        _first_message = False
        return True
    return False








# Initialize the model with the tools
# model = ChatOllama(
#     model="qwen2.5", # For some reason the qwen2.5 model works better than all the other models I tested
#     temperature=0,
#     verbose=False
# ).bind_tools(tools)



# Define the graph
# graph = create_react_agent(model, tools=tools, debug=False, state_modifier=system_prompt)


def print_stream(stream, cache):
    for s in stream:
        # Skip if no messages in the current stream item
        if "messages" not in s or not s["messages"]:
            continue

        message = s["messages"][-1]

        # Handle AI messages with direct content (most important case)
        if hasattr(message, "content") and message.content:

            # Check if the message is a tool message
            if hasattr(message, "__class__") and message.__class__.__name__ == "ToolMessage":
                # Print the name of the tool but not the tool message content
                if hasattr(message, "name"):
                    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (calling tool):{Style.RESET_ALL} {Fore.GREEN}{message.name}(){Style.RESET_ALL}")

            # Only print if it's not a tool message
            if not hasattr(message, "name"):
                print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot 1:{Style.RESET_ALL} {message.content}{Style.RESET_ALL}")

        # Handle AI messages with response_metadata
        if hasattr(message, "response_metadata") and message.response_metadata:
            if message.response_metadata.get("message") and message.response_metadata["message"].get("content"):
                response_string = message.response_metadata["message"]["content"]
                if response_string:  # Only print if there's actual content
                    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot (final response):{Style.RESET_ALL} {response_string}{Style.RESET_ALL}")

        # Handle tool messages
        if hasattr(message, "__class__") and message.__class__.__name__ == "ToolMessage":
            if hasattr(message, "name") and hasattr(message, "content"):
                tool_name = message.name
                tool_content = message.content
                # print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot 4:{Style.RESET_ALL} {Fore.GREEN}Calling tool {tool_name}(){Style.RESET_ALL}")

                # Store in cache with meaningful key
                if tool_name == "get_external_ip":
                    cache = update_cache(cache, "external_ip", tool_content)
                    # print(f"Cache updated with external_ip: {tool_content}")
                elif tool_name == "get_isp_location":
                    cache = update_cache(cache, "location_data", tool_content)
                    # print(f"Cache updated with location_data: {tool_content}")

                # Always store with generic tool name key
                cache = update_cache(cache, tool_name, tool_content)
                # print(f"Cache updated with {tool_name}: {tool_content}")
                save_cache(cache)

    return cache

def main():
    conversation_history: List[Tuple[str, str]] = []

    # Initialize the cache dictionary by loading the cache from the cache file
    cache: Dict[str, Any] = load_cache()

    # Print a message to indicate that the cache has been loaded
    # print(f"{Fore.GREEN}Cache (memories) loaded successfully!{Style.RESET_ALL}")

    # Update the cache with some fundamental information
    if get_cached_value(cache, "os_type") is None:
        update_cache(cache, "os_type", f"{get_os_type()}")
    if get_cached_value(cache, "external_ip") is None:
        update_cache(cache, "external_ip", f"{get_public_ip()}")
    if get_cached_value(cache, "location_data") is None:
        update_cache(cache, "location_data", f"{get_isp_and_location(get_public_ip())}")
    # if get_cached_value(cache, "local_ip") is None:
    #     update_cache(cache, "local_ip", f"{get_local_ip()}")
    # if get_cached_value(cache, "local_date_time") is None:
    #     update_cache(cache, "local_date_time", f"{get_local_date_time_and_timezone()}")
    if get_cached_value(cache, "available_tools") is None:
        update_cache(cache, "available_tools", f"{tools}")


    # Loop through the cache and print the keys and values from the cache file
    # for key, value in cache.items():
    #     print(f"Key: {key}, Value: {value}")


    while True:
        if not check_ollama_status.is_ollama_process_running():
            print(f"{Fore.RED}Ollama process is not running. Please start the Ollama service.{Style.RESET_ALL}")
            check_ollama_status.find_ollama_executable()
            break
        else:
            try:
                user_input = input(f"{Fore.CYAN}\nUser: {Style.RESET_ALL}")

                if user_input.lower() in ["/exit", "/quit"]:
                    print("\nExiting...")
                    save_cache(cache)
                    print("Exiting and saving cache...")
                    break
                
                elif user_input.lower() in ["/help", "help", "/?", "?"]:
                    help_menu_and_list_tools()
                    continue

                elif user_input.lower() == "/clear":
                    # Clear conversation history but keep the system prompt
                    config = {"configurable": {"thread_id": "1"}}
                    memory.delete(config)
                    # Reset first message flag to include system message on next message
                    global _first_message
                    _first_message = True
                    print(f"{Fore.GREEN}Conversation history cleared.{Style.RESET_ALL}")
                    continue
                
                elif user_input.lower() == "/history":
                    # Show the conversation history (for debugging)
                    try:
                        config = {"configurable": {"thread_id": "1"}}
                        # Use get_tuple to get the raw state from memory
                        history_tuple = memory.get_tuple(config)
                        # Convert to dict if needed
                        thread_state = dict(history_tuple) if history_tuple else {}
                        
                        # Ensure we have a valid messages list
                        if isinstance(thread_state, dict) and "messages" in thread_state and isinstance(thread_state["messages"], list):
                            messages = thread_state["messages"]
                            msg_count = len(messages)
                            
                            print(f"{Fore.YELLOW}Conversation history ({msg_count} messages, showing last 5):{Style.RESET_ALL}")
                            
                            # Show at most the last 5 messages
                            for i, msg in enumerate(messages[-5:]):
                                # A safer way to get message type and content
                                msg_class = msg.__class__.__name__ if hasattr(msg, "__class__") else "Unknown"
                                
                                # Different message types
                                if hasattr(msg, "content"):
                                    content = str(msg.content) if msg.content is not None else ""
                                else:
                                    content = str(msg)[:100]
                                
                                # Get role from type or class name
                                if hasattr(msg, "type"):
                                    role = msg.type
                                else:
                                    # Map class names to roles
                                    role_map = {
                                        "HumanMessage": "user",
                                        "AIMessage": "assistant",
                                        "SystemMessage": "system",
                                        "ToolMessage": "tool",
                                        "FunctionMessage": "function"
                                    }
                                    role = role_map.get(msg_class, msg_class)
                                
                                # Add tool information if present
                                if hasattr(msg, "name") and msg.name:
                                    role = f"{role} (tool: {msg.name})"
                                
                                # Create a preview of the content
                                content_preview = (content[:50] + "...") if len(content) > 50 else content
                                
                                # Display message with pretty formatting
                                idx = msg_count - 5 + i if msg_count > 5 else i
                                print(f"{idx}: {Fore.BLUE}{role}{Style.RESET_ALL}: {content_preview}")
                        else:
                            print(f"{Fore.YELLOW}No valid conversation history found.{Style.RESET_ALL}")
                            if "messages" in thread_state:
                                print(f"Messages is type: {type(thread_state['messages'])}")
                    except Exception as e:
                        print(f"{Fore.RED}Error retrieving history: {e}{Style.RESET_ALL}")
                        # Print more debug info for troubleshooting
                        import traceback
                        print(f"{Fore.YELLOW}Debug info: thread_state type: {type(thread_state)}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Debug info: Keys: {thread_state.keys() if isinstance(thread_state, dict) else 'not a dict'}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Traceback: {traceback.format_exc()}{Style.RESET_ALL}")
                        if isinstance(thread_state, dict) and "messages" in thread_state:
                            print(f"Messages type: {type(thread_state['messages'])}")
                            if hasattr(thread_state["messages"], "__iter__"):
                                for i, msg in enumerate(thread_state["messages"][-2:]):
                                    print(f"Message {i} type: {type(msg)}")
                                    print(f"Message {i} attributes: {[attr for attr in dir(msg) if not attr.startswith('_')]}")
                    continue
                    
                elif user_input.lower() == "/tools":
                    # Display a list of available tools
                    def get_first_line(desc):
                        if not desc:
                            return ""
                        lines = desc.split('\n')
                        return lines[0] if lines else ""
                    
                    tools_list = "\n".join([f"- {Fore.GREEN}{tool_object.name}{Style.RESET_ALL}: {get_first_line(tool_object.description)}" 
                                           for tool_object in tools])
                    print(f"{Fore.YELLOW}Available tools:{Style.RESET_ALL}\n{tools_list}")
                    continue
                    
                elif user_input.lower() == "/cache":
                    print(f"{Fore.YELLOW}Cache (memories): {cache}{Style.RESET_ALL}")

                # Create configuration object with thread_id - exactly as shown in LangGraph docs
                config = {"configurable": {"thread_id": "1"}}
                
                # Import all message types we might encounter
                from langchain_core.messages import HumanMessage, SystemMessage
                
                # Create a HumanMessage object from the user input
                user_message = HumanMessage(content=user_input)
                
                # Create input data structure following LangGraph documentation
                # We only add the new message in each call - the checkpointer handles history
                if _is_first_message():
                    # For the first message, include a system message
                    selective_cache = {
                        "os_type": cache.get("os_type", "unknown"),
                        "external_ip": cache.get("external_ip", None),
                        "location_data": cache.get("location_data", None)
                    }
                    # Only include items that are not None
                    selective_cache = {k: v for k, v in selective_cache.items() if v is not None}
                    
                    # Add cache data to system prompt
                    full_system_prompt = f"{system_prompt}\n\nAvailable cached data: {selective_cache}"
                    input_data = {"messages": [SystemMessage(content=full_system_prompt), user_message]}
                else:
                    # For subsequent messages, just add the user message
                    input_data = {"messages": [user_message]}
                
                # Stream the graph with the input_data and config - exactly matching docs
                events = graph.stream(
                    input_data,  # New message(s) to add
                    config,      # Configuration with thread_id
                    stream_mode="values",
                )

                for event in events:
                    event["messages"][-1].pretty_print()







                # Original code with the cache is commented out for now
                # cache = print_stream(response_stream, cache)  # Use the print_stream function to print the response stream
                #
                # save_cache(cache)

            except EOFError:
                print("\nExiting...")
                save_cache(cache)
                print("Exiting and saving cache...")
                break


if __name__ == "__main__":
    main()
