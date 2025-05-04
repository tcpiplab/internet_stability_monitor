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
- **Functions**: Include docstrings for functions, especially tools

## Tool Development
When creating network monitoring tools:
- Add main function with silent/polite params
- Register tool in instability.py
- Create LangChain tools for chatbot integration

## Working Methods
- Rather than having Claude directly test my chatbot after source code modifications, I always prefer to test my chatbot manually in a separate terminal and then I'll tell you the outcome of the testing.