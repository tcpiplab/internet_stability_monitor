# Software Requirements Document: Instability Chatbot v2

## 1. Project Overview

### 1.1 Purpose
The Instability Chatbot v2 is a terminal-based network diagnostic tool that provides an interactive interface for diagnosing and troubleshooting network connectivity issues, even during complete network outages.

### 1.2 Goals
- Create a simpler, more maintainable implementation without LangChain or complex OOP
- Provide offline-capable network diagnostics
- Support all existing diagnostic tools plus previously unintegrated ones
- Offer a user-friendly terminal interface with modern amenities

### 1.3 Target Users
- Hackers and pentesters getting oriented to an unfamiliar local network or environment
- Network administrators
- IT support personnel
- End users troubleshooting network issues
- Developers testing network functionalities

### 1.4 Key Differentiators from v1
- Direct Ollama API integration without LangChain abstraction
- Procedural code design over complex OOP
- Simplified context management using Ollama's native capabilities
- Improved terminal interface with command completion and history

## 2. Core Features

### 2.1 Chatbot Functionality
- Interactive text-based interface for network diagnostic queries
- Multi-turn conversation capability
- Thinking/reasoning display in grey text
- Distinct visual display for tool execution and results
- No emojis or unnecessary visual clutter

### 2.2 Network Diagnostic Capabilities
- Support for all existing diagnostic tools from v1
- Integration of additional diagnostic tools not previously included
- Ability to function fully offline during network outages
- Clear separation between tool interface and implementation

### 2.3 Memory Management
- Use Ollama's native context parameter for conversation history
- Simple file-based cache for storing previous tool results, for example for remembering the most recent external IP address and the date and time it was last checked
- No complex custom memory architecture

### 2.4 Tool Integration
- Direct function-call architecture for tools
- Dynamic discovery and registration of available tools
- Standardized result handling and display
- Ability to call tools directly via commands or by asking the chatbot, for example "/get_external_ip" or "What is my external IP address?"

## 3. Usage Modes

### 3.1 Chatbot Mode
- Interactive conversational interface
- Tool execution based on user queries
- Clear display of tool selection reasoning, execution, and results

### 3.2 Manual Tool Execution
- Direct execution of specific tools via command line
- Structured output of results

### 3.3 Test Mode
- Verification of environment setup, dependencies, API keys in environment variables, and tool availability
- Ollama connectivity testing

## 4. Technical Requirements

### 4.1 Ollama Integration
- Direct use of Ollama Python API
- Utilization of Ollama's context parameter for conversation tracking
- Support for different Ollama models (primarily qwen3:1.7b by default)

### 4.2 Tool Execution Framework
- Simple function-based tool registry
- Standard interface for tool inputs and outputs
- Tool documentation accessible via help command

### 4.3 Caching
- Simple JSON-based cache for tool results
- No custom memory architecture
- Cache should persist between sessions

### 4.4 Error Handling
- Graceful handling of Ollama API errors
- Recovery from tool execution failures
- User-friendly error messages

### 4.5 Offline Operation
- Must function without internet access
- Graceful degradation when online services are unavailable
- Clear indication of online vs. offline capabilities

## 5. User Interface

### 5.1 Terminal Interface
- Color-coded output (via colorama):
  - User input: Cyan
  - Assistant responses: Blue
  - Tool execution: Green
  - Errors: Red
  - Thinking/reasoning: Grey
- Command completion for tools and built-in commands
- Command history navigation with arrow keys

### 5.2 Commands
- `/help`: Display available commands and tools
- `/exit` or `/quit`: Exit the application
- Additional commands as needed for functionality
- Tool-specific commands for direct execution

### 5.3 Output Formatting
- Clear delineation between chatbot responses and tool results
- Visual indication of tool execution in progress
- Proper formatting of multi-line outputs

## 6. Out of Scope

### 6.1 Explicitly Excluded
- LangChain or similar high-level abstraction frameworks
- Complex OOP architecture
- Silent mode (`--silent` option)
- Web or GUI interfaces
- Backward compatibility with v1
- Speech output capabilities

## 7. Performance Requirements

### 7.1 Response Time
- Tool execution should provide feedback within 5 seconds or show progress
- Ollama API responses should be displayed as received

### 7.2 Resource Usage
- Minimal memory footprint
- No background processes or services
- Cache file size limited to reasonable bounds

## 8. Implementation Approach

### 8.1 Code Organization
- Flat, function-based architecture
- Clear separation of concerns
- Minimal dependencies
- Simple file structure:
  - `instability.py`: Main entry point
  - `chatbot.py`: Core chatbot logic
  - `tools.py`: Tool registry and functions
  - `memory.py`: Simple cache management
  - `utils.py`: Helper functions

### 8.2 Dependencies
- Required:
  - `ollama`: For model API access
  - `colorama`: For terminal colors
  - `readline` (or equivalent): For command history and completion
- Optional/conditional dependencies for specific tools

### 8.3 Error Recovery
- Graceful handling of Ollama API failures
- Clear user feedback on tool execution errors
- Operation in degraded modes when resources are unavailable

## 9. Future Considerations

### 9.1 Potential Enhancements
- Plugin architecture for external tools
- Configuration options for model selection
- Option to run groups of tools in sequence, for example, "run all DNS tools"
