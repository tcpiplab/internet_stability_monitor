from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import argparse
import subprocess
from service_check_summarizer import summarize_service_check_output
from tts_utils import speak_text

# Cloud provider status page URLs
cloud_status_pages = {
    "AWS": "https://health.aws.amazon.com/health/status",
    "Google Cloud": "https://status.cloud.google.com/",
    "Azure": "https://status.azure.com/"
}

# Initialize Selenium with Chrome in headless mode
def init_headless_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("window-size=1920,1080")
    
    chrome_service = Service('./drivers/chromedriver')
    
    # Return a new browser session
    return webdriver.Chrome(service=chrome_service, options=chrome_options)

def check_cloud_status(provider, url, browser):
    """Load the status page and retrieve specific elements."""
    try:
        browser.get(url)
        time.sleep(5)  # Give it a few seconds to fully load the page
        
        # AWS check
        if provider == "AWS" and "No recent issues" in browser.find_element(By.TAG_NAME, "body").text:
            return "no issues"

        # Google Cloud check
        elif provider == "Google Cloud":
            try:
                total_services = browser.find_elements(By.CSS_SELECTOR, "svg.psd__status-icon")
                green_checkmarks = browser.find_elements(By.CSS_SELECTOR, "svg.psd__status-icon.psd__available")
                warning_icons = browser.find_elements(By.CSS_SELECTOR, "svg.psd__status-icon.psd__warning")
                
                if not total_services:
                    return "unable to determine status"
                
                percentage_available = len(green_checkmarks) / len(total_services) * 100
                percentage_warning = len(warning_icons) / len(total_services) * 100
                
                # Set a threshold for warnings (e.g., 1%)
                warning_threshold = 1.0
                
                if percentage_available == 100:
                    return "no issues"
                elif percentage_warning > warning_threshold:
                    return f"warning: {percentage_warning:.1f}% services with warnings, {percentage_available:.1f}% fully available"
                elif percentage_available >= 99:  # Adjusted from 90 to 99
                    # return "no significant issues"
                    return "no issues"
                else:
                    return f"issues detected: only {percentage_available:.1f}% services fully available"
            except Exception as e:
                return f"unreachable: {str(e)}"

        # Azure check
        elif provider == "Azure" and "There are currently no active events" in browser.find_element(By.TAG_NAME, "body").text:
            return "no issues"
        
        return "issues detected"
    
    except Exception as e:
        return f"unreachable: {str(e)}"

if __name__ == "__main__":
    # Accept arguments from the command line, such as --silent
    parser = argparse.ArgumentParser(description='Check the status pages of major cloud providers.')
    parser.add_argument('--silent', action='store_true', help='Run in silent mode without voice alerts')
    args = parser.parse_args()

    intro_statement = (
        "Checking the operational status of the primary cloud providers' status pages, "
        "ensuring that all are accessible and do not list any major outages. If any of them were entirely unreachable, "
        "it could indicate a broader infrastructure disruption or a significant service outage at that cloud "
        "platform. This check will run silently and can take up to about one minute. Please stand by..."
    )

    print(f"{intro_statement}")
    if not args.silent:
        speak_text(f"{intro_statement}")

    # Start the browser in headless mode
    browser = init_headless_browser()

    reachable_providers = []
    unreachable_providers = []
    issues_detected = []

    report_on_cloud_platforms = ""

    for provider, url in cloud_status_pages.items():
        result = check_cloud_status(provider, url, browser)
        if "no issues" in result:
            reachable_providers.append(provider)
        elif "unreachable" in result:
            unreachable_providers.append((provider, result))
        else:
            issues_detected.append((provider, result))  # Store both provider and result

    # Clean up
    browser.quit()

    print("Reachable Cloud Providers:")
    report_on_cloud_platforms += "Reachable Cloud Providers:\n"

    for provider in reachable_providers:
        print(f"- {provider}")
        report_on_cloud_platforms += f"- {provider}\n"

    if len(reachable_providers) == len(cloud_status_pages):
        print("Cloud provider reachability summary: All cloud providers are reachable.")
        report_on_cloud_platforms += "\nCloud provider reachability summary: All cloud providers are reachable.\n"

    print("Cloud Providers with No Issues:")
    report_on_cloud_platforms += "\nCloud Providers with No Issues:\n"

    for provider in reachable_providers:
        print(f"- {provider}")
        report_on_cloud_platforms += f"- {provider}\n"

    for provider, status in issues_detected:
        if "no significant issues" in status:
            print(f"- {provider}")
            report_on_cloud_platforms += f"- {provider}\n"

    if len(issues_detected) > 0:
        no_significant_issues = False
        issues_to_report = []

        for provider, status in issues_detected:
            if provider == "Google Cloud" and "no significant issues" in status:
                no_significant_issues = True
                break

        if not no_significant_issues and issues_to_report:
            print("\nCloud Providers with Detected Issues:")
            report_on_cloud_platforms += "\nCloud Providers with Detected Issues:\n"

            for provider, status in issues_to_report:
                print(f"- {provider}: {status}")
                report_on_cloud_platforms += f"- {provider}: {status}\n"

    if len(unreachable_providers) > 0:
        print("\nUnreachable Cloud Providers:")
        report_on_cloud_platforms += "\nUnreachable Cloud Providers:\n"

        for provider, error in unreachable_providers:
            print(f"- {provider}: {error}")
            report_on_cloud_platforms += f"- {provider}: {error}\n"

    cloud_platforms_summary = summarize_service_check_output(report_on_cloud_platforms)
    print(f"{cloud_platforms_summary}")
    if not args.silent:
        speak_text("The cloud platform monitoring report is as follows:")
        speak_text(f"{cloud_platforms_summary}")
