"""
LangGraph agent setup and configuration.

This module sets up the LangGraph agent that powers the chatbot, including
the system prompt, model configuration, and graph structure.
"""

from typing import Dict, Any, List, Callable
from typing_extensions import TypedDict, Annotated

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_messages
from langchain.memory import ConversationBufferMemory

from .planning import PlanningSystem
from .interface import print_ai_message

# Enhanced system prompt that encourages reasoning
ENHANCED_SYSTEM_PROMPT = """
You are an intelligent network diagnostics assistant that combines technical expertise with strong reasoning capabilities.

CAPABILITIES:
1. Analyze user questions deeply to understand their real needs
2. Plan multi-step approaches to complex problems
3. Use tools strategically and combine their outputs
4. Provide explanations that connect technical details to user understanding

APPROACH:
1. First, understand the underlying question or problem
2. Plan what information you need and which tools might help
3. Execute tools thoughtfully, explaining your choices
4. Synthesize all information into a clear, complete answer

You can use multiple tools if needed and should explain your reasoning throughout.
"""

class State(TypedDict):
    """State type for the LangGraph agent."""
    messages: Annotated[list, add_messages]
    plan: Dict[str, Any]
    results: List[Dict[str, Any]]

class EnhancedChatbotAgent:
    """Enhanced LangGraph agent with planning capabilities."""
    
    def __init__(self, 
                 tools: List[Callable], 
                 memory_system,
                 model_name: str = "qwen2.5",
                 system_prompt: str = ENHANCED_SYSTEM_PROMPT):
        """Initialize the enhanced chatbot agent."""
        self.tools = tools
        self.memory = memory_system
        self.model_name = model_name
        self.system_prompt = system_prompt
        
        # Initialize the planning system
        self.planner = PlanningSystem()
        
        # Set up the base model
        self.model = ChatOllama(model=model_name)
        
        # Create a LangChain memory instance using the new format
        self.langchain_memory = ConversationBufferMemory(
            return_messages=True,
            output_key="output",
            input_key="input"
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.model.bind_tools(tools),
            tools=tools,
            memory=self.langchain_memory,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        # Create the enhanced graph
        self.graph = self._create_enhanced_graph()
    
    def _create_enhanced_graph(self):
        """Create an enhanced LangGraph with planning capabilities."""
        
        def planning_node(state: State):
            """Plan the approach for the current query."""
            messages = state["messages"]
            last_message = messages[-1]
            
            if isinstance(last_message, HumanMessage):
                # Create a plan for the query
                context = self.memory.get_context()
                plan = self.planner.create_plan(last_message.content, context)
                return {"plan": plan, "messages": messages}
            return {"plan": state.get("plan", {}), "messages": messages}
        
        def execution_node(state: State):
            """Execute tools based on the plan."""
            plan = state["plan"]
            required_tools = self.planner.evaluate_tool_needs(plan)
            
            results = []
            for tool_name in required_tools:
                if tool_name in [t.name for t in self.tools]:
                    try:
                        tool = next(t for t in self.tools if t.name == tool_name)
                        result = tool.invoke({"input": ""})
                        results.append({"tool": tool_name, "result": result})
                    except Exception as e:
                        print(f"Error executing tool {tool_name}: {e}")
            
            return {
                "results": results,
                "messages": state["messages"],
                "plan": plan
            }
        
        def synthesis_node(state: State):
            """Synthesize results into a coherent response."""
            synthesis = self.planner.synthesize_results(
                state["results"],
                state["messages"][-1].content if state["messages"] else ""
            )
            
            # Add the synthesis as an AI message
            messages = state["messages"] + [AIMessage(content=synthesis)]
            
            return {
                "messages": messages,
                "results": state["results"],
                "plan": state["plan"]
            }
        
        # Build the enhanced graph
        graph = StateGraph(State)
        
        # Add nodes
        graph.add_node("planner", planning_node)
        graph.add_node("executor", execution_node)
        graph.add_node("synthesizer", synthesis_node)
        
        # Add edges with conditional routing
        def route_after_planning(state: State) -> str:
            """Determine next step after planning."""
            plan = state.get("plan", {})
            if plan.get("needs_tools", False):
                return "executor"
            return "synthesizer"
        
        graph.add_conditional_edges(
            "planner",
            route_after_planning,
            {
                "executor": "executor",
                "synthesizer": "synthesizer"
            }
        )
        
        graph.add_edge("executor", "synthesizer")
        graph.add_edge("synthesizer", END)
        graph.add_edge(START, "planner")
        
        # Compile the graph with the LangGraph memory system
        return graph.compile()  # Remove the checkpointer parameter since we're using LangChain memory
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input through the enhanced system."""
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "plan": {},
            "results": []
        }
        
        # Process through the graph
        result = self.graph.invoke(initial_state)
        
        # Update both memory systems
        self.memory.add_interaction(user_input, str(result.get("messages", [])))
        self.langchain_memory.save_context(
            {"input": user_input},
            {"output": str(result.get("messages", []))}
        )
        
        return result
    
    def pretty_print_message(self, message: BaseMessage) -> None:
        """Pretty print a message from the agent."""
        if not message or not hasattr(message, "content"):
            return
            
        # Skip system messages
        if hasattr(message, "type") and message.type == "system":
            return
            
        print_ai_message(message.content)