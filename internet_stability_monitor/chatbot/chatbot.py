"""Chatbot implementation for internet stability monitor.

This module provides a chatbot interface that supports both command-based
and natural language interactions for monitoring internet stability.
"""

from typing import Optional, Dict, List
from datetime import datetime
import re
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
            'exit': self._handle_exit
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
            
            Respond with a JSON array of tool names that would be most relevant to answer the user's question.
            For example: ["dns", "network"] or ["system", "ntp"].
            Only include tools that are directly relevant to the question."""),
            ("user", "{question}")
        ])
        
        # Response generation prompt
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert system administrator and network engineer.
            Your task is to analyze the monitoring results and provide a natural, conversational response to the user's question.
            Use the provided tool outputs to form your response.
            Be concise but informative, and explain any technical terms in simple language.
            If there are any issues or concerns, explain them clearly."""),
            ("user", """Question: {question}
            
            Tool Outputs:
            {tool_outputs}
            
            Please provide a natural response to the user's question based on this information.""")
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
        elif user_input.startswith('//'):
            # Handle double-slash commands for backward compatibility
            cmd, *args = user_input[2:].split(' ', 1)
            args = args[0] if args else ''
            
            if cmd in self.commands:
                return self.commands[cmd](args)
            else:
                return f"Unknown command: {cmd}. Type /help for available commands."
                
        # For natural language queries, use LangChain and Ollama
        try:
            # First, determine which tools to run
            tool_chain = self.tool_prompt | self.ollama | StrOutputParser()
            tools = eval(tool_chain.invoke({"question": user_input}))
            
            # Get outputs from the selected tools
            tool_outputs = self._get_tool_outputs(tools)
            
            # Generate a natural response
            response_chain = self.response_prompt | self.ollama | StrOutputParser()
            response = response_chain.invoke({
                "question": user_input,
                "tool_outputs": tool_outputs
            })
            
            return response
            
        except Exception as e:
            return f"Error processing your question: {str(e)}\nPlease try rephrasing or use a command (type /help for list)." 