"""
Memory management for the chatbot.

This module manages conversation history and memory for the chatbot,
using LangGraph's checkpoint system.
"""

import os
import json
import datetime
from typing import Dict, Any, Optional, List, Union
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Cache file path
CACHE_FILE = os.path.expanduser("~/.instability_cache.json")

class ChatbotMemory:
    """Memory management for the chatbot, handling both LangGraph memory and the cache system."""
    
    def __init__(self, thread_id: str = "1"):
        """Initialize the memory system with the given thread ID."""
        self.thread_id = thread_id
        self.memory = MemorySaver()
        self.cache = self._load_cache()
        self._is_first_message = True
        self._tool_history = []
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load the cache from the cache file."""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                print(f"Chatbot (thinking): Cache loaded from {CACHE_FILE}")
                return cache
            else:
                print(f"Chatbot (thinking): No cache file found at {CACHE_FILE}, creating a new one.")
                return {}
        except Exception as e:
            print(f"Chatbot (thinking): Error loading cache: {e}")
            return {}
    
    def save_cache(self) -> None:
        """Save the cache to the cache file."""
        try:
            # Update the last updated timestamp
            self.cache["cache_last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Chatbot (thinking): Error saving cache: {e}")
    
    def update_cache(self, key: str, value: Any) -> Dict[str, Any]:
        """Update a value in the cache."""
        self.cache[key] = value
        self.save_cache()
        return self.cache
    
    def get_cached_value(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        return self.cache.get(key)
    
    def get_selective_cache(self) -> Dict[str, Any]:
        """Get a selective cache with only essential information."""
        selective_cache = {
            "os_type": self.cache.get("os_type", "unknown"),
            "external_ip": self.cache.get("external_ip", None),
            "location_data": self.cache.get("location_data", None)
        }
        # Only include items that are not None
        return {k: v for k, v in selective_cache.items() if v is not None}
    
    def is_first_message(self) -> bool:
        """Check if this is the first message in the conversation."""
        if self._is_first_message:
            self._is_first_message = False
            return True
        return False
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        config = {"configurable": {"thread_id": self.thread_id}}
        self.memory.delete(config)
        self._is_first_message = True
        self._tool_history = []
    
    def record_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any) -> None:
        """Record a tool call in the history."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._tool_history.append({
            "timestamp": timestamp,
            "tool": tool_name,
            "args": args,
            "result_summary": str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
        })
        
        # Also update the cache to maintain backward compatibility
        self.update_cache(tool_name, result)
    
    def get_tool_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the tool call history, limited to the most recent calls."""
        return self._tool_history[-limit:] if self._tool_history else []
    
    def get_config(self) -> Dict[str, Any]:
        """Get the LangGraph configuration object."""
        return {"configurable": {"thread_id": self.thread_id}}
    
    def create_initial_messages(self, system_prompt: str) -> Dict[str, List]:
        """Create the initial messages for a new conversation."""
        # Add cache data to system prompt if available
        selective_cache = self.get_selective_cache()
        if selective_cache:
            full_system_prompt = f"{system_prompt}\n\nAvailable cached data: {selective_cache}"
        else:
            full_system_prompt = system_prompt
            
        return {"messages": [SystemMessage(content=full_system_prompt)]}
    
    def format_history_output(self) -> str:
        """Format the conversation history for display."""
        config = {"configurable": {"thread_id": self.thread_id}}
        try:
            # Try to get history from LangGraph memory
            history_tuple = self.memory.get_tuple(config)
            
            if not history_tuple:
                return "No conversation history found."
                
            output_lines = [f"Conversation history for thread ID: {self.thread_id}"]
            
            # Most reliable place to look for messages is in the response from a direct invoke
            try:
                from langchain_core.messages import HumanMessage
                response = self.get_direct_history()
                
                if response and "messages" in response:
                    messages = response["messages"]
                    output_lines.append(f"Found {len(messages)} messages in conversation")
                    
                    # Show last 5 messages
                    for i, msg in enumerate(messages[-5:]):
                        msg_type = getattr(msg, "type", type(msg).__name__)
                        content = getattr(msg, "content", str(msg)[:50])
                        output_lines.append(f"{i}: {msg_type} - {content[:50]}...")
                    
                    return "\n".join(output_lines)
            except Exception as e:
                output_lines.append(f"Error getting direct history: {e}")
            
            # If we have tool history, show that
            if self._tool_history:
                output_lines.append("\nTool Call History:")
                for i, call in enumerate(self._tool_history[-5:]):
                    output_lines.append(f"{i}: {call['timestamp']} - {call['tool']}")
                    
            return "\n".join(output_lines)
            
        except Exception as e:
            return f"Error retrieving conversation history: {e}"
    
    def get_direct_history(self) -> Dict[str, Any]:
        """Get history directly from the graph through an invoke call."""
        # This would need a reference to the graph, which isn't available here
        # In the real implementation, this would be passed in or accessed through a different method
        return {"messages": []}  # Placeholder