"""Chatbot implementation for internet stability monitor.

This module provides a chatbot interface that supports both command-based
and natural language interactions for monitoring internet stability.
"""

from typing import Optional, Dict, List
from datetime import datetime
import re
import json
import ast
from colorama import Fore, Style, init
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

from internet_stability_monitor.context import MonitorContext
from internet_stability_monitor.service import MonitorService
from internet_stability_monitor.presentation import MonitorPresenter, DisplayOptions

# Initialize colorama
init(autoreset=True)

class Chatbot:
    """Chatbot for internet stability monitoring."""
    
    def __init__(self, context: MonitorContext):
        """Initialize the chatbot.
        
        Args:
            context: MonitorContext instance
        """
        self.context = context
        self.service = MonitorService(context)
        self.presenter = MonitorPresenter(context)
        self.display_options = DisplayOptions()
        
        # Initialize Ollama
        self.ollama = OllamaLLM(model="mistral")
        
        # Command handlers
        self.commands = {
            'check': self._handle_check,
            'status': self._handle_status,
            'format': self._handle_format,
            'save': self._handle_save,
            'help': self._handle_help,
            'exit': self._handle_exit,
            'config': self._handle_config
        }
        
        # Tool selection prompt
        self.tool_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert system administrator and network engineer.
            Your task is to determine which monitoring tools to run based on the user's question.
            You have access to the following tools:
            - dns: Check DNS resolution and root server availability
            - email: Check email service availability (SMTP/IMAP)
            - whois: Verify WHOIS server accessibility
            - ixp: Monitor Internet Exchange Points (IXPs)
            - cdn: Check Content Delivery Network (CDN) availability
            - cloud: Monitor cloud provider status pages
            - ca: Verify Certificate Authority (CA) endpoint status
            - web: Check major website availability
            - network: Network diagnostics and speed testing
            - ntp: NTP server monitoring
            - system: System service status
            - location: Location and IP information
            
            IMPORTANT: You must respond ONLY with a JSON array containing the tool names.
            DO NOT include any explanation or additional text.
            
            Valid response examples:
            ["dns"]
            ["network","dns"]
            ["location"]
            
            Invalid response examples:
            Based on your question...["location"]
            The tools needed are ["dns","web"]
            {{"tools": ["network"]}}"""),
            ("user", "{question}")
        ])

        
        # Response generation prompt
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert system administrator and network engineer.
            When responding about location information, format the response using the full_location field 
            if available, or construct a response from the individual fields (city, region, country, isp).
            Keep responses concise and professional."""),
            ("user", "{question}"),
            ("assistant", "Here is the relevant information from our monitoring tools: {tool_outputs}"),
        ])


    def _handle_check(self, args: str) -> str:
        """Handle the /check command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        if not args:
            results = self.service.check_all_services()
            return self.presenter.format_results(results)
            
        services = args.split()
        results = {}
        for service in services:
            if service in self.service.check_all_services():
                results[service] = self.service.check_all_services()[service]
        return self.presenter.format_results(results)

    def _handle_status(self, args: str) -> str:
        """Handle the /status command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        results = self.service.check_all_services()
        return self.presenter.format_results(results)

    def _handle_format(self, args: str) -> str:
        """Handle the /format command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        if not args:
            return "Please specify a format (text/json/table)"
            
        format_type = args.lower()
        if format_type not in ['text', 'json', 'table']:
            return "Invalid format. Use text, json, or table"
            
        self.display_options.format = format_type
        self.presenter = MonitorPresenter(self.context, self.display_options)
        return f"Output format changed to {format_type}"

    def _handle_save(self, args: str) -> str:
        """Handle the /save command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        if not args:
            return "Please specify a file path"
            
        try:
            results = self.service.check_all_services()
            with open(args, 'w') as f:
                f.write(self.presenter.format_results(results))
            return f"Results saved to {args}"
        except Exception as e:
            return f"Error saving results: {str(e)}"

    def _handle_help(self, args: str) -> str:
        """Handle the /help command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        help_text = [
            "Available commands (prefixed with /):",
            "  /check [services]  - Check specified services (or all if none specified)",
            "  /status           - Show current system status",
            "  /format [type]    - Change output format (text/json/table)",
            "  /save [file]      - Save current output to file",
            "  /config [action]  - Manage configuration (set/get/list)",
            "  /help             - Show this help message",
            "  /exit             - Exit the program",
            "",
            "You can also ask questions in natural language about your system and network.",
            "For example:",
            "  - Are we using NAT between the LAN and the internet?",
            "  - What's the current network latency?",
            "  - Is my DNS resolution working correctly?",
            "  - What's the status of my email services?"
        ]
        return "\n".join(help_text)

    def _handle_exit(self, args: str) -> str:
        """Handle the /exit command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        return "Goodbye!"

    def _handle_config(self, args: str) -> str:
        """Handle the /config command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response message
        """
        if not args:
            return "Please specify a configuration action (set/get/list)"
            
        parts = args.split()
        if len(parts) < 2:
            return "Please specify a key and value for 'set' command"
            
        action = parts[0].lower()
        if action == 'set':
            key = parts[1]
            value = ' '.join(parts[2:])
            if not value:
                return "Please specify a value to set"
            self.context.cache.update(key, value)
            return f"Configuration updated: {key} = {value}"
        elif action == 'get':
            key = parts[1]
            value = self.context.cache.get(key)
            if value is None:
                return f"No configuration found for key: {key}"
            return f"{key} = {value}"
        elif action == 'list':
            config = self.context.cache.data
            if not config:
                return "No configuration found"
            return "\n".join(f"{k} = {v}" for k, v in config.items())
        else:
            return "Invalid action. Use 'set', 'get', or 'list'"

    def _get_tool_outputs(self, tools: List[str]) -> str:
        """Get outputs from specified tools.
        
        Args:
            tools: List of tool names to run
            
        Returns:
            Formatted tool outputs
        """
        results = self.service.check_all_services()
        outputs = []
        
        for tool in tools:
            if tool in results:
                outputs.append(f"{tool.upper()}:\n{self.presenter.format_results({tool: results[tool]})}")
                
        return "\n\n".join(outputs)


    def process_input(self, user_input: str) -> str:
        """Process user input and return a response.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response message
        """
        # Check if it's a command
        if user_input.startswith('/'):
            cmd, *args = user_input[1:].split(' ', 1)
            args = args[0] if args else ''
            
            if cmd in self.commands:
                return self.commands[cmd](args)
            else:
                return f"Unknown command: {cmd}. Type /help for available commands."

        else:
            # For natural language queries, use LangChain and Ollama
            try:
                print(f"{Fore.YELLOW}Running tool selection prompt...{Style.RESET_ALL}")
                tool_chain = self.tool_prompt | self.ollama | StrOutputParser()
                tools_response = tool_chain.invoke({"question": user_input})
                
                print(f"{Fore.YELLOW}Debug - Raw response from tool chain: {repr(tools_response)}{Style.RESET_ALL}")
                
                # Add validation before parsing
                if not tools_response:
                    raise ValueError("Tool selection returned empty response")
                
                try:
                    print(f"{Fore.YELLOW}Debug - Attempting JSON parse{Style.RESET_ALL}")
                    tools = json.loads(tools_response)
                except json.JSONDecodeError as e:
                    print(f"{Fore.YELLOW}Debug - JSON parse failed: {e}{Style.RESET_ALL}")
                    try:
                        print(f"{Fore.YELLOW}Debug - Attempting ast.literal_eval{Style.RESET_ALL}")
                        tools = ast.literal_eval(tools_response)
                    except (ValueError, SyntaxError) as e:
                        print(f"{Fore.YELLOW}Debug - ast.literal_eval failed: {e}{Style.RESET_ALL}")
                        # Clean up the response
                        cleaned_response = tools_response.strip('`').strip()
                        if cleaned_response.startswith('json'):
                            cleaned_response = cleaned_response[4:]
                        print(f"{Fore.YELLOW}Debug - Cleaned response: {repr(cleaned_response)}{Style.RESET_ALL}")
                        try:
                            tools = json.loads(cleaned_response)
                        except json.JSONDecodeError as e:
                            raise ValueError(f"Could not parse tool selection response: {tools_response}")

                # Ensure tools is a list
                if not isinstance(tools, list):
                    raise TypeError("Tools must be a list")

                print(f"{Fore.YELLOW}Tool selection prompt completed.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Tools: {tools}{Style.RESET_ALL}")
                
                # Validate tools before proceeding
                if not tools:
                    raise ValueError("No tools were selected")
                
                tool_outputs = self._get_tool_outputs(tools)
                
                response_chain = self.response_prompt | self.ollama | StrOutputParser()
                response = response_chain.invoke({
                    "question": user_input,
                    "tool_outputs": tool_outputs
                })
                
                return response

            except ValueError as ve:
                print(f"{Fore.RED}Debug - ValueError: {ve}{Style.RESET_ALL}")
                return f"Invalid input or tool selection: {str(ve)}"
            except TypeError as te:
                print(f"{Fore.RED}Debug - TypeError: {te}{Style.RESET_ALL}")
                return f"Type error in processing: {str(te)}"
            except Exception as e:
                print(f"{Fore.RED}Debug - Unexpected error: {e}{Style.RESET_ALL}")
                return f"Unexpected error: {str(e)}\nPlease try rephrasing or use a command (type /help for list)."



    def run(self) -> None:
        """Run the chatbot in interactive mode."""
        print(f"{Fore.YELLOW}Starting chatbot in interactive mode...{Style.RESET_ALL}")
        while True:
            try:
                print(f"{Fore.YELLOW}Waiting for user input...{Style.RESET_ALL}")
                user_input = input(f"{Fore.CYAN}instability>{Style.RESET_ALL} ").strip()
                if not user_input:
                    continue
                    
                print(f"{Fore.YELLOW}Processing input: {user_input}{Style.RESET_ALL}")
                response = self.process_input(user_input)
                print(response)
                
                if user_input.lower() == '/exit':
                    break
                    
            except KeyboardInterrupt:
                print("\nStopping monitor...")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
                print("Please try again or type /help for available commands.") 