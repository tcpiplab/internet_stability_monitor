"""
LangGraph agent setup and configuration.

This module sets up the LangGraph agent that powers the chatbot, including
the system prompt, model configuration, and graph structure.

The agent includes:
1. ReAct-based reasoning for network diagnostics
2. Tool providers for organizing available tools
3. Anti-recursion detection to prevent infinite loops (see route_agent function)
4. Error handling and debug logging
"""

from typing import Dict, Any, List, Callable, Optional, TypeVar, Protocol, Pattern
from typing_extensions import TypedDict, Annotated
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re
import os
import datetime
from colorama import Fore, Style

# LangSmith integration
# If LANGCHAIN_TRACING_V2 is set to true in environment variables, this will enable LangSmith tracing
# If you've already configured LangSmith env vars in your ~/.zshrc, you don't need to set them here
# Required env vars: LANGCHAIN_API_KEY, LANGCHAIN_PROJECT, LANGCHAIN_ENDPOINT (optional)
langsmith_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"

# Only import langsmith if tracing is enabled
if langsmith_enabled:
    from langsmith import Client
    client = Client()
    print(f"{Style.DIM}LangSmith tracing enabled for project: {os.environ.get('LANGCHAIN_PROJECT', 'default')}{Style.RESET_ALL}")
else:
    # If not using LangSmith, disable warnings
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["LANGCHAIN_CALLBACKS_BACKGROUND"] = "false"
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="langsmith.client")
from langchain_core.tools import BaseTool, tool
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Create our own ToolExecutor since it seems to be missing
class ToolExecutor:
    """Tool executor class."""
    
    def __init__(self, tools):
        """Initialize with a list of tools."""
        self.tools = {tool.name: tool for tool in tools}
    
    def invoke(self, input_dict):
        """Invoke a tool with inputs."""
        tool_name = input_dict.pop("tool_name")
        tool = self.tools.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool {tool_name} not found. Available tools: {list(self.tools.keys())}")

        print(f"{Fore.LIGHTBLUE_EX}Chatbot (Executing tool):{Fore.RESET} Invoking {tool_name} with input: {input_dict}")

        return tool.invoke(input_dict)
from langchain.agents import AgentExecutor
# Removed deprecated ConversationBufferMemory import
from langchain.agents.agent import AgentFinish, AgentAction
# Removed hub import since we're using a local prompt template
from langchain.agents import create_react_agent
from langchain.agents.format_scratchpad import format_log_to_str

# Type for tool results
ToolResult = TypeVar('ToolResult')

# Helper functions for colored output
def debug_print(message: str) -> None:
    """Print a debug message in gray color."""
    # Disable debug prints for cleaner output
    # print(f"{Style.DIM}DEBUG: {message}{Style.RESET_ALL}")
    pass

def warning_print(message: str) -> None:
    """Print a warning message in yellow color."""
    print(f"{Fore.YELLOW}WARNING: {message}{Style.RESET_ALL}")
    
def error_print(message: str) -> None:
    """Print an error message in red color."""
    print(f"{Fore.RED}ERROR: {message}{Style.RESET_ALL}")

def trace_in_langsmith(name: str, func, *args, run_type: str = "chain", tags: List[str] = None, metadata: Dict[str, Any] = None, **kwargs):
    """Helper function to trace arbitrary code in LangSmith if enabled.
    
    Args:
        name: Name of the trace
        func: Function to trace
        run_type: Type of run (chain, llm, tool, etc.)
        tags: List of tags to apply to the trace
        metadata: Dictionary of metadata to add to the trace
        args, kwargs: Arguments to pass to the function
        
    Returns:
        The result of calling func with the provided arguments
    """
    if not langsmith_enabled:
        return func(*args, **kwargs)
    
    try:
        from langsmith import trace
        result = None
        
        # Execute the function within the trace context
        with trace(
            name=name,
            run_type=run_type,
            tags=tags or [],
            metadata=metadata or {}
        ):
            result = func(*args, **kwargs)
            
            # Optionally add the result to metadata if needed in the future
            # Note: We don't use add_output anymore as it's not supported
        
        return result
    except Exception as ls_error:
        debug_print(f"LangSmith tracing error in {name}: {ls_error}")
        return func(*args, **kwargs)  # Fall back to running without tracing

class ToolProvider(Protocol):
    """Protocol for tool providers that can be added to the agent."""
    
    @property
    def tools(self) -> List[BaseTool]:
        """Get the tools provided by this provider."""
        ...
    
    @property
    def name(self) -> str:
        """Get the name of this tool provider."""
        ...

@dataclass
class State:
    """State type for the LangGraph agent."""
    messages: List[BaseMessage]
    current_tool: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[str] = None
    intermediate_steps: List[tuple] = None
    last_question: Optional[str] = None  # The last question asked by the bot
    pending_tools: List[str] = None  # Tools mentioned in the last question
    raw_thinking: Optional[str] = None  # Raw thinking steps from the model

    def __post_init__(self):
        if self.intermediate_steps is None:
            self.intermediate_steps = []
        if self.pending_tools is None:
            self.pending_tools = []

class ChatbotAgent:
    """Enhanced LangGraph agent with extensible tool support."""
    
    def __init__(self, 
                 tool_providers: List[ToolProvider],
                 memory_system: Any,
                 model_name: str = "qwen3:8b",
                 max_iterations: int = 10) -> None:
        """Initialize the chatbot agent."""
        self.tool_providers = tool_providers
        self.memory = memory_system
        self.model_name = model_name
        self.max_iterations = max_iterations
        
        # Collect all tools from providers
        self.tools: List[BaseTool] = []
        for provider in tool_providers:
            self.tools.extend(provider.tools)
        
        # Set up the base model
        self.model = ChatOllama(model=model_name)
        
        # We're using our own memory system instead of deprecated ConversationBufferMemory
        # This aligns with the LangGraph approach recommended in the migration guide
        
        # Create a local ReAct prompt template instead of pulling from the hub
        # This ensures the chatbot can function without internet access
        react_prompt = ChatPromptTemplate.from_messages([
            ("system", """Assistant is a network diagnostics specialist built to help troubleshoot connectivity issues.

Assistant is designed to help diagnose and resolve network connectivity and stability problems. It has knowledge of networking concepts, protocols, and common issues that can affect internet connections. As a network specialist, Assistant can analyze various aspects of a network connection, identify potential issues, and recommend solutions.

Assistant can evaluate different layers of network connectivity, from physical connections to application-level services. It can help troubleshoot problems with DNS, latency, packet loss, and other networking issues. Assistant is especially skilled at interpreting the results of diagnostic tools and explaining them in an understandable way.

TOOLS:
------

Assistant has access to the following tools:

{tools}

To use a tool, please use the following format EXACTLY - DO NOT use any other format or tags like <think>:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use THIS EXACT format and NO other format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

IMPORTANT:
1. ALWAYS use the exact formats above - never use <think> tags or any other format
2. ALWAYS prefix your thoughts with "Thought:", actions with "Action:", and final answers with "Final Answer:"
3. Keep your thoughts focused on determining which tool to use or interpreting results
4. For the ping_target tool, provide the hostname or IP directly as the input

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}"""),
        ])
        
        # Create the agent using create_react_agent with our local prompt
        self.agent = create_react_agent(
            llm=self.model,
            tools=self.tools,
            prompt=react_prompt
        )
        
        # Set tracing tags for LangSmith if enabled
        self.tracing_tags = None
        if langsmith_enabled:
            self.tracing_tags = {
                "agent_type": "internet_stability_chatbot",
                "model": self.model_name,
                "project": os.environ.get("LANGCHAIN_PROJECT", "default")
            }
        
        # Create the graph
        self.graph = self._create_graph()
    
    def _create_system_prompt(self) -> str:
        # This method can potentially be removed or adapted if needed for ReAct prompt customization
        return ""

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph execution graph."""
        # Create tool executor
        tool_executor = ToolExecutor(tools=self.tools)
        
        # Define graph nodes
        def agent_node(state: State) -> Dict[str, Any]:
            """Run the agent to decide the next action."""
            
            # --- ADJUST FOR REACT AGENT ---
            # Format intermediate steps for the ReAct agent scratchpad
            scratchpad = format_log_to_str(state.intermediate_steps)

            # Prepare input for agent.invoke
            agent_inputs = {
                "input": state.messages[-1].content,
                "chat_history": state.messages[:-1],
                "agent_scratchpad": scratchpad,
                "intermediate_steps": state.intermediate_steps # Add intermediate_steps directly
            }

            # Custom wrapper to handle mixed output with both actions and final answers
            try:
                # Capture raw model output with thinking before parsing
                raw_thinking = None
                try:
                    # Create a direct prompt based on the ReactPrompt
                    direct_prompt = {"input": agent_inputs["input"],
                                    "chat_history": agent_inputs["chat_history"],
                                    "agent_scratchpad": agent_inputs["agent_scratchpad"]}

                    # Get raw LLM response with the same inputs
                    raw_response = self.model.invoke([
                        SystemMessage(content=f"""You are a network diagnostics assistant that helps troubleshoot connectivity issues.
                        When answering, FIRST put your detailed thinking process inside <think>...</think> tags.
                        THEN use the ReAct format as specified. Available tools: {[tool.name for tool in self.tools]}"""),
                        HumanMessage(content=f"User question: {agent_inputs['input']}\n\nPrevious conversation: {agent_inputs['chat_history']}")
                    ])

                    if raw_response and hasattr(raw_response, 'content'):
                        raw_thinking = raw_response.content

                        # Print thinking immediately, instead of waiting until the end
                        think_match = re.search(r"<think>(.*?)</think>", raw_thinking, re.DOTALL)
                        if think_match:
                            from .interface import print_ai_thinking
                            print_ai_thinking(think_match.group(1).strip())

                        # Still store for later reference
                        state.raw_thinking = raw_thinking
                except Exception as think_err:
                    debug_print(f"Failed to capture raw thinking: {think_err}")

                # Standard parser attempt
                result = self.agent.invoke(agent_inputs)

                # Store the thinking in the log property
                if hasattr(result, 'log') and raw_thinking:
                    # For AgentAction and AgentFinish, include the raw thinking
                    result.log = f"<think>{raw_thinking}</think>\n\n{result.log}" if result.log else f"<think>{raw_thinking}</think>"

            except Exception as e:
                if "Parsing LLM output produced both a final answer and a parse-able action" in str(e):
                    debug_print("Detected mixed output with both action and final answer")
                    
                    # Get the raw LLM output directly from the error message
                    # The error should contain the full output that caused the parsing issue
                    # If not, we need to examine it via debug methods
                    
                    # Since we can't easily get the raw output from the LLM response that caused the error,
                    # we'll manually recreate the output based on the patterns the parser is using
                    raw_output = str(e)
                    
                    # If we can't extract useful information from the error message,
                    # call the LLM directly with a more explicit instruction
                    if "Parsing LLM output" in raw_output and len(raw_output) < 200:
                        debug_print("Error message doesn't contain full output, making direct LLM call")
                        # Create a simpler prompt to get a direct response
                        direct_messages = [
                            SystemMessage(content="You are a network diagnostics assistant that can use tools to help users."),
                            HumanMessage(content=f"Previous conversation: {state.messages[:-1]}\n\nUser question: {state.messages[-1].content}\n\nYou have these tools available: {[tool.name for tool in self.tools]}\n\nRespond in ReAct format with EITHER an Action OR a Final Answer, not both.")
                        ]
                        raw_output = self.model.invoke(direct_messages).content

                        # Try to extract and display thinking from the direct call
                        think_match = re.search(r"<think>(.*?)</think>", raw_output, re.DOTALL)
                        if think_match:
                            from .interface import print_ai_thinking
                            print_ai_thinking(think_match.group(1).strip())
                    
                    # Get the patterns directly in case the parser doesn't expose the methods we need
                    action_pattern = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
                    final_answer_pattern = r"Final Answer: (.*)"
                    
                    # Try to extract action first - this makes the agent more proactive
                    action_match = re.search(action_pattern, raw_output, re.DOTALL)
                    
                    try:
                        # Try to use the agent's parser methods if available
                        if hasattr(self.agent.output_parser, "get_action_match"):
                            action_match = self.agent.output_parser.get_action_match(raw_output)
                    except Exception as parser_error:
                        debug_print(f"Couldn't use agent parser methods: {parser_error}")
                    
                    if action_match:
                        # There's an action, prioritize it over the final answer
                        tool_name = action_match.group(1).strip()
                        
                        # Extract action input, providing empty dict as fallback
                        action_input = "{}"
                        try:
                            # Try to use the output parser's method if available
                            if hasattr(self.agent.output_parser, "get_action_input_match"):
                                action_input_match = self.agent.output_parser.get_action_input_match(raw_output)
                                if action_input_match:
                                    action_input = action_input_match.group(1).strip()
                            else:
                                # Use our own regex as fallback
                                action_input = action_match.group(2).strip() if len(action_match.groups()) > 1 else "{}"
                        except Exception as input_error:
                            debug_print(f"Error extracting action input: {input_error}")
                        
                        # Parse action input to dict if possible
                        try:
                            if hasattr(self.agent.output_parser, "parse_action_input"):
                                action_input_dict = self.agent.output_parser.parse_action_input(action_input)
                            else:
                                # Simple parsing fallback
                                import json
                                try:
                                    action_input_dict = json.loads(action_input)
                                except json.JSONDecodeError:
                                    action_input_dict = {"input": action_input}
                        except Exception:
                            # If parsing fails, use the raw string
                            action_input_dict = {"input": action_input}
                            
                        # Create an AgentAction manually
                        debug_print(f"Manually extracted action: {tool_name} with input: {action_input_dict}")
                        
                        # Fix specific issues with ping_target tool - it expects a string as target
                        if tool_name == "ping_target":
                            # For ping_target specifically, handle various input formats
                            if isinstance(action_input_dict, dict):
                                if not action_input_dict or action_input_dict.get('input') == '{}' or action_input_dict == {}:
                                    debug_print(f"Error: ping_target requires a target parameter. Fixing by using fallback.")
                                    # Prevent executing ping with invalid arguments
                                    result = AgentFinish(
                                        return_values={"output": "I need a specific hostname or IP address to ping. Can you please provide one?"},
                                        log="Fixed invalid ping_target call"
                                    )
                                    return result
                                elif 'input' in action_input_dict and isinstance(action_input_dict['input'], str):
                                    # Extract target from the input string if possible
                                    if action_input_dict['input'].strip() in ['{}', '()', '[]', '']:
                                        debug_print(f"Error: ping_target requires a target parameter. Fixing by using fallback.")
                                        # Prevent executing ping with invalid arguments
                                        result = AgentFinish(
                                            return_values={"output": "I need a specific hostname or IP address to ping. Can you please provide one?"},
                                            log="Fixed invalid ping_target call"
                                        )
                                        return result
                                    # If input contains a valid string that looks like an IP or hostname, transform to direct string
                                    valid_input = action_input_dict['input'].strip()
                                    # Leave as is - the tool execution will handle this correctly now
                            elif isinstance(action_input_dict, str):
                                # For direct string input, leave as is - handled by the tool execution now
                                if action_input_dict.strip() in ['{}', '()', '[]', '']:
                                    debug_print(f"Error: ping_target requires a valid target parameter.")
                                    result = AgentFinish(
                                        return_values={"output": "I need a specific hostname or IP address to ping. Can you please provide one?"},
                                        log="Fixed invalid ping_target call"
                                    )
                                    return result
                        
                        result = AgentAction(tool=tool_name, tool_input=action_input_dict, log=raw_output)
                    else:
                        # No action found, look for final answer
                        final_answer_match = re.search(final_answer_pattern, raw_output, re.DOTALL)
                        
                        try:
                            # Try to use the agent's parser methods if available
                            if hasattr(self.agent.output_parser, "get_final_answer_match"):
                                final_answer_match = self.agent.output_parser.get_final_answer_match(raw_output)
                        except Exception as parser_error:
                            debug_print(f"Couldn't use agent parser methods: {parser_error}")
                        
                        if final_answer_match:
                            answer = final_answer_match.group(1).strip()
                            debug_print(f"Manually extracted final answer: {answer}")
                            result = AgentFinish(return_values={"output": answer}, log=raw_output)
                        else:
                            # Neither found clearly - default to treating as a final answer
                            debug_print(f"Could not extract action or answer cleanly, treating as final answer")
                            result = AgentFinish(return_values={"output": raw_output}, log=raw_output)
                else:
                    # Re-raise if it's a different error
                    raise

            # --- Define tools known to take NO arguments ---
            no_arg_tools = {
                "get_external_ip",
                "get_local_ip",
                "get_isp_location",
                "check_external_ip_change",
                "check_internet_connection",
                "check_layer_three_network",
                "check_dns_resolvers",
                "check_ollama",
                "get_os",
                "check_cdn_reachability",
                "check_whois_servers",
                "check_tls_ca_servers",
                "check_smtp_servers",
                "run_mac_speed_test", # Technically takes args, but often called without by agent
                "check_dns_root_servers_reachability",
                "check_local_layer_two_network",
                "check_websites"
            }

            # Handle the result (keep AgentFinish/AgentAction logic)
            if isinstance(result, AgentFinish):
                # Extract the output content
                output_content = result.return_values["output"]
                
                # Check if the response contains a question that might need follow-up
                question_markers = [
                    "would you like me to", "would you like to", "do you want me to",
                    "should i", "shall i", "do you want to", "would you prefer",
                    "would you like", "do you want", "should we", "shall we"
                ]
                
                # List of tools that might be mentioned in questions
                tool_names = [
                    "get_external_ip", "get_local_ip", "check_external_ip_change", 
                    "check_internet_connection", "check_layer_three_network",
                    "check_dns_resolvers", "check_websites", "check_dns_root_servers_reachability",
                    "check_local_layer_two_network", "check_cdn_reachability", "check_whois_servers",
                    "check_tls_ca_servers", "check_smtp_servers", "run_mac_speed_test"
                ]
                
                # Convert tool names to more readable format for text matching
                readable_tool_names = [name.replace("_", " ").replace("check ", "").replace("get ", "") for name in tool_names]
                
                # Look for question patterns
                output_lower = output_content.lower()
                is_question = False
                pending_tools = []
                
                if "?" in output_content:
                    for marker in question_markers:
                        if marker in output_lower:
                            is_question = True
                            # Try to identify mentioned tools
                            for i, readable_name in enumerate(readable_tool_names):
                                if readable_name in output_lower:
                                    pending_tools.append(tool_names[i])
                            break
                
                # Final response - mark as complete, but track if it's a question
                return {
                    "messages": state.messages + [AIMessage(content=output_content)],
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None,
                    "last_question": output_content if is_question else None,
                    "pending_tools": pending_tools,
                    "raw_thinking": state.raw_thinking  # Ensure raw_thinking is passed through
                }
            elif isinstance(result, AgentAction):
                # --- Intercept and correct tool input if necessary ---
                agent_tool_input = result.tool_input
                actual_tool_input = agent_tool_input # Default to agent's provided input

                if result.tool in no_arg_tools:
                    # If the target tool takes no args, force input to {}
                    # regardless of what the agent provided (null, (), etc.)
                    debug_print(f"Overriding input for no-arg tool '{result.tool}'. Agent provided: {agent_tool_input}")
                    actual_tool_input = {}
                elif isinstance(agent_tool_input, dict) and list(agent_tool_input.keys()) == ['input']:
                    # Handle cases where agent might wrap a single string argument 
                    # in {'input': 'some_value'} for tools that expect a direct string.
                    # This might need refinement based on tool specifics.
                    debug_print(f"Unwrapping potential single string input for tool '{result.tool}'. Agent provided: {agent_tool_input}")
                    actual_tool_input = agent_tool_input['input'] 
                # Note: If tool expects complex dict input, ensure agent provides it correctly

                # Next action - use the potentially corrected actual_tool_input
                return {
                    "messages": state.messages, # Keep messages as is
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": result.tool,
                    "tool_input": actual_tool_input, # Use the corrected input
                    "tool_output": None,
                    "last_question": state.last_question,  # Preserve last question
                    "pending_tools": state.pending_tools  # Preserve pending tools
                }
            else:
                # Unexpected result type - mark as complete
                error_msg = f"Unexpected agent result type: {type(result)}"
                return {
                    "messages": state.messages + [AIMessage(content=error_msg)],
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None,
                    "last_question": None,  # No question in error case
                    "pending_tools": [],  # No pending tools in error case
                    "raw_thinking": state.raw_thinking
                }
        
        def tool_node(state: State) -> Dict[str, Any]:
            """Execute the selected tool."""
            if not state.current_tool or state.tool_input is None:
                # Include last_question and pending_tools in the returned state
                return {
                    **state.__dict__,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None,
                    "last_question": state.last_question,
                    "pending_tools": state.pending_tools,
                    "raw_thinking": state.raw_thinking
                }
            
            # Prepare tool input, handling potential placeholders from the agent
            actual_tool_input = state.tool_input
            if isinstance(actual_tool_input, dict) and list(actual_tool_input.keys()) == ['input'] and actual_tool_input['input'] == '()':
                 # Check if the actual tool (from self.tools) expects arguments. 
                 # This is complex, so for now, assume empty dict if input is '()' placeholder
                 debug_print(f"Tool {state.current_tool} received placeholder input {actual_tool_input}, assuming no args needed.")
                 actual_tool_input = {} 

            debug_print(f"Executing tool: {state.current_tool} with processed input: {actual_tool_input}")
            
            # Execute the tool
            try:
                # Prepare the input based on its type - handling strings specially
                if isinstance(actual_tool_input, str):
                    # For string inputs, create appropriate parameter mapping
                    if state.current_tool == "ping_target":
                        # The ping_target tool expects a "target" parameter
                        tool_executor_input = {"tool_name": state.current_tool, "target": actual_tool_input}
                    else:
                        # For other tools receiving a string, use "input" as default parameter
                        tool_executor_input = {"tool_name": state.current_tool, "input": actual_tool_input}
                elif isinstance(actual_tool_input, dict):
                    # For dict inputs, use them directly
                    tool_executor_input = {"tool_name": state.current_tool, **actual_tool_input}
                else:
                    # For other types (should be rare), convert to string
                    tool_executor_input = {"tool_name": state.current_tool, "input": str(actual_tool_input)}
                
                debug_print(f"Final tool input: {tool_executor_input}")
                result = tool_executor.invoke(tool_executor_input)
                debug_print(f"Tool {state.current_tool} result: {result}")
                
                # Record the tool call in memory
                self.memory.record_tool_call(state.current_tool, actual_tool_input, result)
                
                # Log successful tool execution to LangSmith if enabled
                if langsmith_enabled:
                    try:
                        # Create a trace for this specific tool call
                        from langsmith import trace
                        with trace(
                            name=f"Tool: {state.current_tool}",
                            run_type="tool",
                            tags=["tool_execution", state.current_tool],
                            metadata={
                                "tool_name": state.current_tool,
                                "tool_input": str(actual_tool_input),
                                "tool_output": str(result)[:1000] if result else ""
                            }
                        ) as run:
                            # Note: previously we were using run.add_output() but this is no longer supported
                            pass
                    except Exception as ls_error:
                        debug_print(f"LangSmith tool tracing error: {ls_error}")
                
                # Create the success action tuple for intermediate steps
                action_tuple = (AgentAction(tool=state.current_tool, tool_input=actual_tool_input, log=""), str(result))
                new_steps = state.intermediate_steps + [action_tuple]
                
                # Add debug logging to help detect patterns in tool usage
                if len(new_steps) >= 2:
                    prev_tool = new_steps[-2][0].tool if len(new_steps) >= 2 else "none"
                    debug_print(f"Tool sequence: {prev_tool} -> {state.current_tool}")

                    # Define tools that commonly get stuck in loops and their response templates
                    direct_result_tools = {
                        "get_os": "We are running {result}.",
                        "get_external_ip": "Our external IP address is {result}.",
                        "get_local_ip": "Our local IP address is {result}.",
                        "check_internet_connection": "Internet connection status: {result}.",
                        "check_layer_three_network": "Layer 3 network status: {result}."
                    }

                    # Check if current tool is in the list and the same one was called previously
                    if state.current_tool in direct_result_tools and prev_tool == state.current_tool:
                        # Get the appropriate response template and format with the result
                        response_template = direct_result_tools[state.current_tool]
                        response_message = response_template.format(result=result)

                        debug_print(f"Detected repeated {state.current_tool} calls, returning result directly")
                        return {
                            "messages": state.messages + [AIMessage(content=response_message)],
                            "intermediate_steps": new_steps,
                            "current_tool": None,
                            "tool_input": None,
                            "tool_output": str(result),
                            "last_question": None,
                            "pending_tools": [],
                            "raw_thinking": state.raw_thinking
                        }

                return {
                    "messages": state.messages,
                    "intermediate_steps": new_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": str(result),
                    "last_question": state.last_question,  # Preserve last question
                    "pending_tools": state.pending_tools,  # Preserve pending tools
                    "raw_thinking": state.raw_thinking
                }
            except Exception as e:
                error_print(f"Error executing tool {state.current_tool} with input {actual_tool_input}: {e}") 
                error_msg = f"Error executing {state.current_tool}: {str(e)}"
                
                # Create the failure action tuple safely
                # Use the potentially modified actual_tool_input
                failed_action_tuple = (AgentAction(tool=state.current_tool, tool_input=actual_tool_input, log=f"Tool execution failed: {error_msg}"), f"Tool execution failed: {error_msg}")
                new_steps = state.intermediate_steps + [failed_action_tuple]
                
                return {
                    "messages": state.messages + [AIMessage(content=error_msg)],
                    "intermediate_steps": new_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None,
                    "last_question": None,  # No question in error case
                    "pending_tools": [],  # No pending tools in error case
                    "raw_thinking": state.raw_thinking
                }
        
        # Build the graph
        workflow = StateGraph(State)
        
        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tool", tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Define conditional routing logic
        def route_agent(state: State) -> str:
            """Determine the next step after the agent node."""
            if state.current_tool:
                # Check maximum iterations
                if len(state.intermediate_steps) >= self.max_iterations:
                    state.messages.append(AIMessage(content=f"Reached max iterations ({self.max_iterations}). Finishing."))
                    return END
                
                # Enhanced tool loop detection with multiple patterns
                if len(state.intermediate_steps) >= 3:
                    # Get recent tool calls (more than 3 to detect more complex patterns)
                    recent_tools = [step[0].tool for step in state.intermediate_steps[-6:]] if len(state.intermediate_steps) >= 6 else [step[0].tool for step in state.intermediate_steps]
                    
                    # 1. Check for the same tool being called consecutively (original check)
                    if len(recent_tools) >= 3 and len(set(recent_tools[-3:])) == 1 and recent_tools[-1] == state.current_tool:
                        warning_msg = f"Detected repetitive calls to the same tool '{state.current_tool}'. This might indicate an infinite loop. Stopping execution."
                        warning_print(warning_msg)
                        state.messages.append(AIMessage(content=warning_msg))
                        return END
                    
                    # 2. Check for ping-pong pattern between two tools (ABAB pattern)
                    if len(recent_tools) >= 4:
                        # Check if there's a repeating pattern of 2 tools
                        tool_pairs = zip(recent_tools[::2], recent_tools[1::2]) # Group tools in pairs
                        tool_pairs = list(tool_pairs)
                        
                        if len(tool_pairs) >= 2:
                            # If the pairs are identical, we've found a ping-pong pattern
                            if tool_pairs[0] == tool_pairs[1] and (tool_pairs[0][0] == state.current_tool or tool_pairs[0][1] == state.current_tool):
                                tools_involved = list(set(tool_pairs[0]))
                                warning_msg = f"Detected ping-pong pattern between tools {tools_involved}. This might indicate an infinite loop. Stopping execution."
                                warning_print(warning_msg)
                                state.messages.append(AIMessage(content=warning_msg))
                                return END
                    
                    # 3. Check for a tool being called too many times overall
                    if len(recent_tools) >= 5:
                        tool_counts = {}
                        for tool in recent_tools:
                            tool_counts[tool] = tool_counts.get(tool, 0) + 1
                        
                        # If any tool (including current) is being called more than 50% of the time
                        for tool, count in tool_counts.items():
                            if count >= len(recent_tools) * 0.5 and tool == state.current_tool:
                                warning_msg = f"Tool '{tool}' has been called {count} times in the last {len(recent_tools)} steps. This might indicate an infinite loop. Stopping execution."
                                warning_print(warning_msg)
                                state.messages.append(AIMessage(content=warning_msg))
                                return END
                
                return "tool"
            else:
                return END
        
        # Add conditional edges from agent node
        workflow.add_conditional_edges(
            "agent",
            route_agent,
            {
                "tool": "tool",
                END: END
            }
        )
        
        # Add edge from tool node back to agent node
        workflow.add_edge("tool", "agent")
        
        # Compile the graph
        return workflow.compile()
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input using the LangGraph agent."""
        # Get the last conversation state if available from memory
        last_state = None
        try:
            history = self.memory.get_direct_history()
            if history and isinstance(history, dict) and "last_state" in history:
                last_state = history["last_state"]
        except Exception as e:
            debug_print(f"Error retrieving last state: {e}")
            last_state = None
        
        # Check if the user's response is a simple yes/no to a previous question
        is_continuing_conversation = False
        pending_tools = []
        modified_input = user_input
        
        # Try to get the last_state from memory cache
        if not last_state:
            try:
                cached_last_state = self.memory.get_cached_value("last_state")
                if cached_last_state and isinstance(cached_last_state, dict):
                    debug_print("Retrieved last_state from cache")
                    last_state = cached_last_state
            except Exception as e:
                debug_print(f"Error retrieving cached last_state: {e}")
                last_state = None
                
        # Initialize user_input_lower here to ensure it's always available
        user_input_lower = user_input.lower().strip()
        
        if last_state and isinstance(last_state, dict):
            last_question = last_state.get("last_question")
            pending_tools = last_state.get("pending_tools", [])
            
            debug_print(f"Last question: {last_question is not None}, Pending tools: {pending_tools}")
            
            if last_question and pending_tools:
                # Check for affirmative responses
                affirmative_responses = ["yes", "yes please", "sure", "okay", "ok", "yep", "yeah", "please do", "go ahead"]
                negative_responses = ["no", "no thanks", "nope", "don't", "do not"]
                
                if any(user_input_lower == resp for resp in affirmative_responses):
                    is_continuing_conversation = True
                    
                    # For tool-specific responses we'll directly run the tools
                    if len(pending_tools) == 1:
                        # If only one tool is pending, we'll call it directly
                        debug_print(f"Directly executing tool: {pending_tools[0]}")
                        modified_input = f"Please run the {pending_tools[0].replace('_', ' ')} tool and tell me the results."
                    elif len(pending_tools) == 2:
                        # If two tools are pending, we'll call both with comparison
                        debug_print(f"Directly comparing tools: {pending_tools}")
                        tool_names = " and ".join([t.replace("_", " ") for t in pending_tools])
                        modified_input = f"Please run the {tool_names} tools and compare the results."
                    else:
                        # If multiple tools, create a more general request
                        tool_names = ", ".join([t.replace("_", " ") for t in pending_tools])
                        modified_input = f"Yes, please run {tool_names} as you suggested in your previous message."
                    
                    debug_print(f"Modified input: '{modified_input}'")
                    
                elif any(user_input_lower == resp for resp in negative_responses):
                    # This is a negative response - we should acknowledge it but not run any tools
                    # Just pass through the original input with context
                    modified_input = f"No, I don't want to {', '.join([t.replace('_', ' ') for t in pending_tools])}. Please continue."
                    debug_print(f"Modified negative input: '{modified_input}'")
                    
            # Handle special commands to reset context
            elif user_input_lower in ["/reset", "reset context", "start over", "forget previous"]:
                # Clear the last state and pending tools
                self.memory.update_cache("last_state", None)
                debug_print("Reset conversation context and memory")
                modified_input = "Let's start a new conversation. Previous context has been reset."
                
            # Only add context if it's clearly a continuation of the conversation
            # Simply starting a new question shouldn't add the previous context
            elif last_question and user_input_lower not in ["help", "/help", "exit", "/exit", "quit", "/quit"]:
                # Check if this appears to be a direct follow-up to the last question
                if (user_input_lower.startswith(("yes", "no", "ok", "sure", "can you", "what about", "how about"))
                    or any(ref in user_input_lower for ref in ["that", "this", "it", "those", "these", "what you mentioned", "your suggestion"])):
                    # Add context from the last question to ensure continuity
                    question_summary = last_question.split("\n")[0][:50]  # Take first line, truncate if too long
                    modified_input = f"Regarding your question about '{question_summary}', my response is: {user_input}"
                    debug_print(f"Added context to user input: '{modified_input}'")
                    
        # Prepare initial state
        initial_state = State(
            messages=[HumanMessage(content=modified_input)],
            intermediate_steps=[],  # Ensure intermediate_steps is initialized as empty list
            last_question=None,  # Reset the last question
            pending_tools=[]  # Reset pending tools
        )
        
        final_state: Optional[Dict[str, Any]] = None
        try:
            # Invoke the graph
            # Set recursion_limit slightly higher to allow the graph to reach END naturally
            debug_print("Invoking graph...")
            
            # Configure graph invocation with LangSmith tracing if enabled
            config = {"recursion_limit": self.max_iterations + 5}
            
            # Add LangSmith metadata if tracing is enabled
            if langsmith_enabled and self.tracing_tags:
                run_name = f"Chatbot Run - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                config["configurable"] = {
                    "tags": self.tracing_tags,
                    "metadata": {
                        "user_input": modified_input,
                        "is_continuation": is_continuing_conversation
                    },
                    "run_name": run_name
                }
                
            # Invoke the graph with the configured settings
            final_state = self.graph.invoke(initial_state, config=config)
            debug_print(f"Graph invocation complete. Final state type: {type(final_state)}")
        except Exception as e:
            error_str = str(e)
            error_print(f"Error invoking graph: {error_str}")
            
            if "Parsing LLM output produced both a final answer and a parse-able action" in error_str:
                # This error is now handled by our custom parser, but provide a helpful message
                # if the error somehow propagates up to here
                return {
                    "response": "I noticed you asked about something that required me to both provide information and take an action. Let me try that again more carefully.",
                    "intermediate_steps": []
                }
            else:
                # Other errors
                return {
                    "response": f"An error occurred during graph processing: {error_str}",
                    "intermediate_steps": []
                }

        final_response_message = "No response generated."
        final_intermediate_steps = []

        if final_state: # Check if final_state is not None and is a dict (implicitly checked by .get)
            debug_print(f"Processing final state: {final_state}")
            messages = final_state.get('messages', []) # Use .get() for safety
            if messages:

                 # Ensure messages is a list before proceeding
                 if isinstance(messages, list):
                     ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
                     if ai_messages:
                         final_response_message = ai_messages[-1].content
                 else:
                     warning_print(f"Expected 'messages' to be a list, but got {type(messages)}")
            else:
                 debug_print("No 'messages' key found in final state or it was empty.")

            final_intermediate_steps = final_state.get('intermediate_steps', []) # Use .get()
            debug_print(f"Final response: {final_response_message}")
            debug_print(f"Final intermediate steps: {final_intermediate_steps}")

            # Save context only if processing was potentially successful (even if no response generated)
            try:
                debug_print("Saving context to memory...")
                
                # Save the conversation state with last_question and pending_tools
                last_state = {
                    "last_question": final_state.get("last_question"),
                    "pending_tools": final_state.get("pending_tools", [])
                }
                
                # Save to our custom memory system
                # This replaces the deprecated ConversationBufferMemory approach
                self.memory.add_interaction(user_input, final_response_message)
                
                # Store last state in the direct memory cache
                # We're using the cache system built into ChatbotMemory instead of the MemorySaver put_tuple
                self.memory.update_cache("last_state", last_state)
                
                # Save the cache
                self.memory.save_cache()
                
                debug_print(f"Context saved with last_question: {last_state['last_question'] is not None}")
                if last_state["last_question"]:
                    debug_print(f"Pending tools: {last_state['pending_tools']}")
            except Exception as e:
                 error_print(f"Error saving context to memory: {e}")

        else:
             warning_print("final_state was None after graph invocation.")

        # Extract thinking from raw LLM output
        thinking_content = None

        if final_state and hasattr(final_state, 'raw_thinking') and final_state.raw_thinking:
            # Extract content between <think> tags - using non-greedy match to get the first complete think block
            think_match = re.search(r"<think>(.*?)</think>", final_state.raw_thinking, re.DOTALL)
            if think_match:
                thinking_content = think_match.group(1).strip()
            else:
                # Try alternate format with "Thought:" prefix
                thought_match = re.search(r"Thought:(.*?)(?:Action:|Final Answer:)", final_state.raw_thinking, re.DOTALL)
                if thought_match:
                    thinking_content = thought_match.group(1).strip()

        # Fallback to intermediate steps if no raw thinking
        thinking_steps = []

        if not thinking_content:
            for step in final_intermediate_steps:
                # Each step is a tuple of (AgentAction, result)
                if isinstance(step[0], AgentAction):
                    # Extract thought portion from the log (everything before Action:)
                    log = step[0].log
                    thought_match = re.search(r"Thought:(.*?)(?:Action:|$)", log, re.DOTALL)
                    if thought_match:
                        thinking = thought_match.group(1).strip()
                        if thinking:
                            thinking_steps.append(thinking)

        return {
            "response": final_response_message,
            "intermediate_steps": final_intermediate_steps,
            "thinking": thinking_content,
            "thinking_steps": thinking_steps
        }
    
    def pretty_print_message(self, message: BaseMessage) -> None:
        """Pretty print a message based on its type."""
        if isinstance(message, HumanMessage):
            print(f"User: {message.content}")
        elif isinstance(message, AIMessage):
            print(f"Chatbot: {message.content}")
        elif isinstance(message, SystemMessage):
            print(f"System: {message.content}")
        else:
            print(message)