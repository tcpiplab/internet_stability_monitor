import requests
import json


def summarize_service_check_output(output_text):
    """
    Summarize the service_check monitoring output using Ollama API.
    
    Args:
        output_text (str): The output text from the monitoring script.
    
    Returns:
        str: A summary of the service_check monitoring output.
    """

    # print(f"Will try summarizing the monitoring output: \n---\n{output_text}\n---\n")

    payload = {
        "model": "mistral",
        "prompt": output_text,
        # "system": "Summarize the result of the monitoring and highlight any issues",
        "system": "Summarize the result of the monitoring and highlight any issues. "
                  "Summarize only based on the provided monitoring report. "
                  "Do not include assumptions or information that was not explicitly stated in the original report. "
                  "Your summary must only be in the form of sentences and paragraphs. "
                  "Do not use bullets or numbering.",
        "stream": False,
        "max_tokens": 20,
        "temperature": 0.2,
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post('http://localhost:11434/api/generate', headers=headers, data=json.dumps(payload))
        # print(f"Got response from Ollama API: {response.text}")
        response.raise_for_status()

        try:
            summary = response.json().get('response', 'No summary available.')
            # print(f"Summary: {summary}")
            return summary

        except json.JSONDecodeError:
            print("Failed to parse the JSON response. Please check the response format.")
            summary = "No summary available due to parsing error."
            return summary

    except requests.RequestException as e:
        print(f"Failed to get summary from Ollama API: {e}")
        summary = f"Failed to get summary from Ollama API: {e}"
        return summary
