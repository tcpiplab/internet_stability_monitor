# Internet Stability Monitor Chatbot

This package contains a modular implementation of the Internet Stability Monitor's chatbot feature, powered by LangChain, LangGraph, and Ollama.

## Architecture

The chatbot is divided into several modular components:

- **main.py**: Entry point and main loop
- **agent.py**: LangGraph agent setup and configuration
- **memory.py**: Conversation history and memory management
- **tools.py**: Network diagnostic tools
- **commands.py**: Command handlers (/help, /exit, etc.)
- **interface.py**: Terminal UI and formatting

## Key Features

- **Unified Memory System**: Uses LangGraph's `MemorySaver` for persistent conversation history
- **Tool History Tracking**: Records all tool calls with timestamps
- **Command Handler**: Implements common commands with proper error handling
- **Modular Design**: Easy to extend with new tools or commands

## Commands

- **/help**: Show available commands and tools
- **/exit** or **/quit**: Exit the chatbot
- **/clear**: Clear conversation history
- **/history**: View conversation history 
- **/memory**: Display detailed memory state
- **/tools**: List all available tools
- **/cache**: Show cached data
- **/tool_history**: Show history of tool calls

## Development

To add a new tool:

1. Add the tool function to `tools.py`
2. Ensure it calls `memory_system.record_tool_call()` 
3. Add it to the `get_tools()` function

To add a new command:

1. Add the command handler in `commands.py`
2. Register it in the `handle_command()` function