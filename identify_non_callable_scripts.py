#!/usr/bin/env python3
import os

# Step 1: List all Python scripts with "check" in their names
check_scripts = [f for f in os.listdir('.') if f.endswith('.py') and 'check' in f]

# Step 2: Identify callable tools in chatbot mode
callable_tools = []
with open('chat_langchain_ollama_agent.py', 'r') as file:
    for line in file:
        if '@tool' in line:
            # Read the next line to get the function name
            next_line = next(file).strip()
            if 'def ' in next_line:
                # Extract the function name
                function_name = next_line.split('def ')[1].split('(')[0]
                # Convert function name to script name
                script_name = function_name.replace('_', '') + '.py'
                callable_tools.append(script_name)

# Step 3: Compare the lists
non_callable_scripts = set(check_scripts) - set(callable_tools)

print("Python scripts with 'check' in their names that are not callable as tools:")
for script in non_callable_scripts:
    print(f"- {script}")
