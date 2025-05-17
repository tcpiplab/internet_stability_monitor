# Instability Chatbot v2

A terminal-based network diagnostic assistant that provides an interactive interface for diagnosing and troubleshooting network connectivity issues, even during complete network outages.

## Overview

Instability v2 is a complete rewrite of the original network diagnostic chatbot, designed with simplicity and maintainability in mind. It features:

- Direct Ollama API integration without LangChain abstraction
- Procedural code design over complex OOP
- Simplified conversation management
- Improved terminal interface with command completion and history
- Offline capability for diagnostics during network outages

## Key Improvements Over v1

- **Simpler Architecture**: Function-based design instead of complex class hierarchies
- **Fewer Dependencies**: Minimal external dependencies, mainly just Ollama and colorama
- **Better Maintainability**: Clear separation of concerns with a modular design
- **Enhanced Reliability**: Graceful degradation when services are unavailable
- **Improved UX**: Command history, completion, and color-coded interface

## Installation

### Requirements

- Python 3.7 or higher
- [Ollama](https://ollama.ai/) installed and running locally
- The `qwen3:8b` model installed in Ollama

### Setting Up

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Ensure Ollama is running:

```bash
ollama serve
```

4. Make sure the qwen3:8b model is available:

```bash
ollama pull qwen3:8b
```

## Usage

### Running the Chatbot

```bash
python instability.py chatbot
```

### Running Specific Tools Manually

```bash
python instability.py manual [tool_name]
```

To see a list of available tools:

```bash
python instability.py manual
```

To run all tools:

```bash
python instability.py manual all
```

### Testing the Environment

```bash
python instability.py test
```

### Getting Help

```bash
python instability.py help
```

## In-Chat Commands

While using the chatbot, you can use these commands:

- `/help` - Show available commands and tools
- `/exit` or `/quit` - Exit the chatbot
- `/clear` - Clear conversation history
- `/tools` - List available diagnostic tools
- `/cache` - Display cached data
- `/<tool_name>` - Run a specific tool directly (e.g., `/get_local_ip`)

## Project Structure

- `instability.py` - Main entry point and CLI interface
- `chatbot.py` - Core chatbot functionality and Ollama integration
- `tools.py` - Tool registry and diagnostic functions
- `memory.py` - Simple cache management
- `utils.py` - Helper functions and UI utilities
- `requirements.txt` - Project dependencies
- `Instability_Chatbot_SRD.md` - Software Requirements Document
- `Instability_ASCII_Header.txt` - ASCII art header for the terminal interface

## Design Principles

This implementation follows these key principles:

1. **Simplicity**: Function-based architecture without complex OOP
2. **Maintainability**: Clear separation of concerns with minimal interdependencies
3. **Reliability**: Graceful degradation during network issues
4. **Usability**: Intuitive interface with helpful feedback
5. **Offline Operation**: Critical functions work without internet access

## Dependencies

- `ollama`: For interfacing with local LLM
- `colorama`: For colorized terminal output
- `readline` (Unix/macOS) or `pyreadline3` (Windows): For command history and completion

## Extending the Tools

To add a new diagnostic tool:

1. Add your function to `tools.py`
2. Ensure it has a clear docstring explaining its purpose
3. Add the function to the tool registry in the `get_available_tools()` function

The tool will automatically be available to both the chatbot and the manual mode.

## Troubleshooting

### Ollama Connection Issues

If you encounter issues connecting to Ollama:

1. Ensure Ollama is running with `ollama serve`
2. Verify the qwen3:8b model is installed with `ollama list`
3. Check for any firewalls blocking localhost connections

### Command History Not Working

On Windows, ensure pyreadline3 is installed:

```bash
pip install pyreadline3
```

On Unix/Linux/macOS, the built-in readline should work automatically.