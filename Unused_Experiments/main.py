import subprocess
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.agents.mrkl.output_parser import MRKLOutputParser
from langchain_core.prompts import PromptTemplate
from ollama_llm import OllamaLLM
from tools import tools
import requests

class CustomOllamaLLM(OllamaLLM):
    def _llm_type(self):
        return "custom_llm_type"

    def _call(self, prompt, stop=None, **kwargs):
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": prompt,
            "stream": False,
            "temperature": 0.2,
        }

        print(f"Calling Ollama API with payload: {payload}")

        response = requests.post(url, json=payload)

        print(f"Ollama API response: {response.text}")

        if response.status_code != 200:
            raise RuntimeError(f"Ollama API call failed: {response.text}")
        return response.json().get("output", "")
        # return response.json().get("response", "")

class CustomOutputParser(MRKLOutputParser):
    def parse(self, text: str):
        # Ensure 'Action:' is present after 'Thought:'
        if "Thought:" in text and "Action:" not in text:
            text = text.replace("Thought:", "Thought:\nAction:")
        return super().parse(text)

def main():
    # Create an instance of our Ollama LLM wrapper
    llm = CustomOllamaLLM(
        model_name="llama2:latest",  # adjust as needed
        ollama_path="ollama"     # adjust if ollama is not in PATH
    )

    # Initialize an agent with the tools and custom output parser
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
    )

    print("Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower().strip() in ["exit", "quit", "q"]:
            break
        elif user_input.lower().strip() == "clear":
            print("\n" * 100)
            continue
        elif user_input.strip() == "":
            continue
        elif user_input.lower().strip() == "help":
            print("Type 'exit' to quit.")
            continue
        response = agent.run(user_input)
        print("Agent:", response)

if __name__ == "__main__":
    main()