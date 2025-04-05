"""
LangChain/Ollama agent for internet stability monitoring.

This is a wrapper that imports the modularized chatbot code.
Kept for backward compatibility.
"""

from internet_stability_monitor.chatbot.main import main as chatbot_main

# Main entry point - kept for backward compatibility
def main():
    """Run the chatbot."""
    chatbot_main()

if __name__ == "__main__":
    main()