# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run the chatbot: `python instability.py chatbot`
- Run all checks: `python instability.py manual all`
- Run specific check: `python instability.py manual [check_name]`
- Run tests: `python instability.py test`

## Code Style Guidelines
- **Imports**: Standard library imports first, then third-party, then local modules
- **Typing**: Use Python type hints (from typing import List, Dict, Optional, etc.)
- **Naming**: 
  - snake_case for functions/variables
  - CamelCase for classes
  - UPPERCASE for constants
- **Error Handling**: Use try/except blocks with specific exceptions
- **Logging**: Print statements should use colorama (Fore.COLOR)
- **Comments**: Minimal comments, focusing on why not what
- **Functions**: Include verbose, thorough docstrings for functions, especially for tools that can be called by the chatbot

## Project Architecture
- **Function-based Design**: Project uses procedural programming rather than complex OOP
- **Core Components**:
  - `instability.py`: Main entry point and CLI interface
  - `chatbot.py`: Handles Ollama interactions and chat session logic
  - `tools.py`: Network diagnostic tools with original and fallback implementations
  - `memory.py`: Simple cache management
  - `utils.py`: UI and helper functions

## Tool Development
When creating network monitoring tools:
- Add main function with silent/polite params
- Register tool in `get_available_tools()` in tools.py
- Include clear docstrings explaining their purpose
- Implement fallback behavior for offline operation

## Dependencies
- Ollama Python API
- colorama for terminal colors
- pyreadline3 (Windows only) for command history

## Working Methods
- Rather than having Claude directly test my chatbot after source code modifications, I always prefer to test my chatbot manually in a separate terminal and then I'll tell you the outcome of the testing.