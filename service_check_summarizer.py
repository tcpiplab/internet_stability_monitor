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

    payload = {
        "model": "mistral",
        "prompt": output_text,
        "system": "Summarize the result of the monitoring and highlight any issues",
        "stream": False,
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post('http://localhost:11434/api/generate', headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        try:
            summary = response.json().get('response', 'No summary available.')
        except json.JSONDecodeError:
            print("Failed to parse the JSON response. Please check the response format.")
            summary = "No summary available due to parsing error."

        return summary

    except requests.RequestException as e:
        print(f"Failed to get summary from Ollama API: {e}")
        return None