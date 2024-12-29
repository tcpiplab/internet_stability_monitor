import subprocess
from langchain.llms.base import LLM
from typing import Optional, List


class OllamaLLM(LLM):
    model_name: str = "llama3.1:latest"  # Example, replace with your model name/identifier
    ollama_path: str = "ollama"  # Path to the ollama CLI, if not on PATH adjust accordingly

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        # Call Ollama with the prompt.
        # For Ollama: `ollama run <model> -p <prompt>`
        # Adjust the command as per Ollama CLI usage if different.
        cmd = [self.ollama_path, "run", self.model_name, "--prompt", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Ollama call failed: {result.stderr}")

        # Ollama might return a response with prompts intermixed;
        # Adjust parsing as needed depending on Ollama’s output format.
        output = result.stdout.strip()
        return output

    @property
    def _identifying_params(self):
        return {"model_name": self.model_name}