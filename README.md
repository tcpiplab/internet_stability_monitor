

# Internet Stability Monitor

This project is designed to monitor various aspects of internet stability including DNS checks, NTP synchronization, email alerts, website response, and WHOIS data checks. It is optimized for macOS and is intended to be run manually using the `run_all.py` script.

## Modes of Operation

The project can be run in several modes:

1. **Chatbot Mode**: Run the interactive chatbot using the command `python instability.py chatbot`.
2. **Manual Mode**: Run all scripts manually using the command `python instability.py manual`.
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

## macOS Optimization

- **Bandwidth Test**: The project uses the proprietary macOS command (exact command needs to be added) to test network bandwidth, ensuring accurate results on macOS systems.
- **Speech Summary**: The `say` command is utilized to read a summary of the test results out loud.
- **Local LLM Summary**: A local instance of Ollama running the `mistral` LLM is used to create a summary of the monitoring results. Ensure Ollama is installed and properly configured on your macOS system.

## Installation

1. Ensure you have Python 3.12.7 installed on your macOS system.
2. Clone the repository to your local machine.
3. Install the required packages using pip:

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
