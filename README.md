
# instability.py

The **`instability.py`** tool is designed to assess various aspects of local network connectivity and 
the overall stability of external internet infrastructure and services. 

The chatbot mode is intended to be useful for anyone wanting a quick and easy way to check the status of their 
network or of worldwide internet infrastructure.

AI developers may also be interested in experimenting with how different models understand (or don't quite understand) 
network analysis at various OSI layers and monitoring of critical internet infrastructure services like DNS, NTP, HTTP, SMTP, IMAP, WHOIS, etc.


## Key Features

- **Chatbot Mode**: Utilize an interactive chatbot built with **Ollama**, the **qwen2.5** model (recommended), and 
  **LangChain**. This mode runs locally, eliminating the need for cloud-based API tokens, and allows you to query your network and internet infrastructure in real-time.

- **Comprehensive Monitoring**: Perform a wide range of checks to gain insights into your internet's performance and stability.

- **Cross Platform**: The tool runs on macOS, Linux, Windows, or WSL. But currently the speed test feature only 
  works on macOS.

- **Optional Speech Summary**: In manual mode you will get a summary of the monitoring results read out loud using 
  the built-in text-to-speech feature on macOS or Windows. Linux should work too but you may need to install a TTS 
  engine like `espeak`. The TTS feature can be disabled with `--silent`.

## Modes of Operation

The project can be run in several modes:

1. **Chatbot Mode**: Run the interactive chatbot using the command `python instability.py chatbot`.
2. **Manual Mode**: Run any one or all scripts manually using the command `python instability.py manual`.
3. **Test Mode**: Run tests using the command `python instability.py test`.
4. **Help**: Display help information using the command `python instability.py help`.


## Directory Structure

The project contains the following main files and modules:

- `dns_check.py`: Handles DNS resolution checks.
- `monitor.py`: Core module to execute and log checks.
- `ntp_check.py`: Checks NTP synchronization status.
- `web_check.py`: Verifies website availability and response.
- `whois_check.py`: Retrieves WHOIS information for domains.
- `process_logs.py`: Processes and analyzes log data.
- `run_all.py`: Main entry point to run all checks.
- `check_local_os.py`: Checks the local operating system status.
- `report_source_location.py`: Reports the source of issues.
- `mac_speed_test.py`: Tests network speed on macOS.
- `cloud_check.py`: Checks the status of various cloud services.
- `cdn_check.py`: Verifies the status of Content Delivery Networks.
- `imap_check.py`: Monitors IMAP email server status.


## Installation

1. Ensure you have Python <= 3.12.7 installed on your system. Note that very new versions of Python, such as 3.
   13.1 may not be compatible with all dependencies.
2. Make sure you already have [Ollama](https://ollama.com/) installed, running, and that you have downloaded the `qwen2.5` model:
   
    ```bash
    ollama pull qwen2.5
    ollama serve 
    ```

3. Clone the repository to your local machine.
    
    ```bash
    git clone <this repo url>
    cd internet_stability_monitor
    ```
4. Create a virtual environment and activate it:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

5. Install the required packages using pip:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

To execute the tool, use the `instability.py` script with the desired mode:

```bash
python instability.py <mode>
```

This script will call the necessary modules and generate a report based on the results of the checks.

## Contributing

If you wish to contribute to this project, please fork the repository and submit a pull request. Ensure that your code adheres to the project's coding standards and include appropriate tests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to all contributors and the open-source community for their valuable resources and tools.

## Installing Ollama and the Mistral Model on macOS

To use the local LLM summary feature, you'll need to install Ollama on your macOS system and download the `mistral` model. Follow these steps:

1. **Install Ollama**:
   
   Visit the [Ollama website](https://ollama.com/) and follow the instructions to download and install the Ollama software on your macOS.

2. **Download the Mistral Model**:

   Once you have Ollama installed, you can download the `mistral` model by running the following command:

   ```bash
   ollama pull mistral
   ```

   Ensure that the paths and necessary configurations are correctly set up so the `process_logs.py` script can interact with Ollama to generate summaries.

These steps will enable the project to utilize local LLM capabilities for summarizing log files and integrating with the overall workflow.

## Setting Up ChromeDriver

To run Selenium tests, you need to have the correct version of `chromedriver` installed. Follow these steps to download and set up `chromedriver`:

1. **Check Your Chrome Version**:

   Open Chrome and navigate to `chrome://settings/help` to find your Chrome browser version.

2. **Download ChromeDriver**:

   Visit the [ChromeDriver download page](https://googlechromelabs.github.io/chrome-for-testing/) and download the version that matches your Chrome browser.

3. **Save ChromeDriver**:

   After downloading the `chromedriver`, unzip the file and save the `chromedriver` executable to the `./drivers` directory in your project root.

4. **Verify Path**:

   Ensure that the `./drivers` directory contains the `chromedriver` file. The structure should look like this:
   ```text
   internet_stability_monitor/
   ├── drivers/
   │   └── chromedriver
   └── README.md
   ```

   By following these steps, you ensure that Selenium has the appropriate WebDriver to interact with Chrome for your test automation.
